"""
Redis Conversation Threading Helper

Manages conversation context and threading across platforms using Redis.
Handles multi-level threading, working memory, and context preservation.
"""

import asyncio
import json
import uuid
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging

# Simple logger setup to avoid dependency issues during development
logger = logging.getLogger("redis_helper")


class ThreadType(Enum):
    """Types of conversation threads"""
    TWITTER = "twitter"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    CROSS_PLATFORM = "cross_platform"
    MAYA_INTERNAL = "maya_internal"


class MessageRole(Enum):
    """Message roles in conversation"""
    USER = "user"
    MAYA = "maya"
    CEREBRAS = "cerebras"
    SYSTEM = "system"


@dataclass
class ConversationMessage:
    """Individual message in a conversation thread"""
    id: str
    thread_id: str
    role: MessageRole
    content: str
    platform: str
    metadata: Dict[str, Any]
    timestamp: datetime
    parent_message_id: Optional[str] = None
    sentiment: Optional[str] = None
    entities: List[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Redis storage"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['role'] = self.role.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationMessage':
        """Create from dictionary"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['role'] = MessageRole(data['role'])
        return cls(**data)


@dataclass
class ConversationThread:
    """Conversation thread containing multiple messages"""
    id: str
    type: ThreadType
    title: str
    participants: List[str]
    platform_data: Dict[str, Any]
    messages: List[ConversationMessage]
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True
    context_summary: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Redis storage"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        data['expires_at'] = self.expires_at.isoformat() if self.expires_at else None
        data['type'] = self.type.value
        data['messages'] = [msg.to_dict() for msg in self.messages]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationThread':
        """Create from dictionary"""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        data['expires_at'] = datetime.fromisoformat(data['expires_at']) if data['expires_at'] else None
        data['type'] = ThreadType(data['type'])
        data['messages'] = [ConversationMessage.from_dict(msg) for msg in data['messages']]
        return cls(**data)


class RedisConversationHelper:
    """
    Redis-based conversation threading and context management
    
    Features:
    - Multi-level conversation threading
    - Cross-platform conversation tracking
    - TTL-based memory cleanup
    - Context summarization and preservation
    - Working memory management for Cerebras
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.redis_url = config.get('redis_url', 'redis://localhost:6379')
        self.redis_db = config.get('redis_db', 0)
        self.default_ttl = config.get('default_ttl', 3600 * 24 * 7)  # 7 days
        self.working_memory_ttl = config.get('working_memory_ttl', 3600)  # 1 hour
        
        self.redis_client = None
        self._use_stub = config.get('use_stub', True)
        
        if not self._use_stub:
            self._initialize_redis()
        else:
            logger.warning("Redis helper running in stub mode")
            self._stub_storage = {}  # In-memory storage for stub mode
    
    def _initialize_redis(self):
        """Initialize Redis connection"""
        try:
            import redis.asyncio as redis
            self.redis_client = redis.from_url(
                self.redis_url,
                db=self.redis_db,
                decode_responses=True
            )
            logger.info("Redis connection initialized")
        except ImportError:
            logger.warning("Redis not available, using stub mode")
            self._use_stub = True
            self._stub_storage = {}
    
    # Thread Management
    
    async def create_thread(self, 
                          thread_type: ThreadType,
                          title: str,
                          platform_data: Dict[str, Any],
                          participants: List[str] = None,
                          ttl: Optional[int] = None) -> ConversationThread:
        """
        Create a new conversation thread
        
        Args:
            thread_type: Type of thread
            title: Thread title
            platform_data: Platform-specific data
            participants: List of participant IDs
            ttl: Time to live in seconds
            
        Returns:
            Created conversation thread
        """
        thread_id = str(uuid.uuid4())
        now = datetime.utcnow()
        expires_at = now + timedelta(seconds=ttl or self.default_ttl)
        
        thread = ConversationThread(
            id=thread_id,
            type=thread_type,
            title=title,
            participants=participants or [],
            platform_data=platform_data,
            messages=[],
            created_at=now,
            updated_at=now,
            expires_at=expires_at
        )
        
        await self._store_thread(thread)
        
        logger.info(f"Created conversation thread: {thread_id}")
        return thread
    
    async def get_thread(self, thread_id: str) -> Optional[ConversationThread]:
        """
        Get conversation thread by ID
        
        Args:
            thread_id: Thread ID
            
        Returns:
            Conversation thread or None
        """
        if self._use_stub:
            thread_data = self._stub_storage.get(f"thread:{thread_id}")
            if thread_data:
                return ConversationThread.from_dict(thread_data)
            return None
        
        try:
            thread_data = await self.redis_client.get(f"thread:{thread_id}")
            if thread_data:
                return ConversationThread.from_dict(json.loads(thread_data))
            return None
        except Exception as e:
            logger.error(f"Failed to get thread {thread_id}: {e}")
            return None
    
    async def update_thread(self, thread: ConversationThread) -> bool:
        """
        Update conversation thread
        
        Args:
            thread: Thread to update
            
        Returns:
            Success status
        """
        thread.updated_at = datetime.utcnow()
        return await self._store_thread(thread)
    
    async def delete_thread(self, thread_id: str) -> bool:
        """
        Delete conversation thread
        
        Args:
            thread_id: Thread ID
            
        Returns:
            Success status
        """
        if self._use_stub:
            self._stub_storage.pop(f"thread:{thread_id}", None)
            return True
        
        try:
            await self.redis_client.delete(f"thread:{thread_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete thread {thread_id}: {e}")
            return False
    
    # Message Management
    
    async def add_message(self, 
                        thread_id: str,
                        role: MessageRole,
                        content: str,
                        platform: str,
                        metadata: Dict[str, Any] = None,
                        parent_message_id: Optional[str] = None,
                        sentiment: Optional[str] = None,
                        entities: List[Dict[str, Any]] = None) -> Optional[ConversationMessage]:
        """
        Add message to conversation thread
        
        Args:
            thread_id: Thread ID
            role: Message role
            content: Message content
            platform: Platform name
            metadata: Additional metadata
            parent_message_id: Parent message ID for threading
            sentiment: Message sentiment
            entities: Extracted entities
            
        Returns:
            Created message or None
        """
        thread = await self.get_thread(thread_id)
        if not thread:
            logger.error(f"Thread {thread_id} not found")
            return None
        
        message_id = str(uuid.uuid4())
        message = ConversationMessage(
            id=message_id,
            thread_id=thread_id,
            role=role,
            content=content,
            platform=platform,
            metadata=metadata or {},
            timestamp=datetime.utcnow(),
            parent_message_id=parent_message_id,
            sentiment=sentiment,
            entities=entities or []
        )
        
        thread.messages.append(message)
        
        if await self.update_thread(thread):
            logger.info(f"Added message {message_id} to thread {thread_id}")
            return message
        
        return None
    
    async def get_thread_messages(self, 
                                thread_id: str,
                                limit: Optional[int] = None,
                                since: Optional[datetime] = None) -> List[ConversationMessage]:
        """
        Get messages from thread
        
        Args:
            thread_id: Thread ID
            limit: Maximum number of messages
            since: Only messages after this time
            
        Returns:
            List of messages
        """
        thread = await self.get_thread(thread_id)
        if not thread:
            return []
        
        messages = thread.messages
        
        # Filter by time
        if since:
            messages = [msg for msg in messages if msg.timestamp > since]
        
        # Sort by timestamp
        messages.sort(key=lambda x: x.timestamp)
        
        # Apply limit
        if limit:
            messages = messages[-limit:]
        
        return messages
    
    # Context Management
    
    async def get_conversation_context(self, 
                                     thread_id: str,
                                     max_messages: int = 10) -> Dict[str, Any]:
        """
        Get conversation context for AI processing
        
        Args:
            thread_id: Thread ID
            max_messages: Maximum messages to include
            
        Returns:
            Conversation context
        """
        thread = await self.get_thread(thread_id)
        if not thread:
            return {}
        
        recent_messages = thread.messages[-max_messages:]
        
        # Build context
        context = {
            'thread_id': thread_id,
            'thread_type': thread.type.value,
            'title': thread.title,
            'participants': thread.participants,
            'platform_data': thread.platform_data,
            'message_count': len(thread.messages),
            'recent_messages': [
                {
                    'role': msg.role.value,
                    'content': msg.content,
                    'platform': msg.platform,
                    'timestamp': msg.timestamp.isoformat(),
                    'sentiment': msg.sentiment,
                    'entities': msg.entities
                }
                for msg in recent_messages
            ],
            'context_summary': thread.context_summary,
            'last_updated': thread.updated_at.isoformat()
        }
        
        return context
    
    async def update_context_summary(self, 
                                   thread_id: str, 
                                   summary: str) -> bool:
        """
        Update conversation context summary
        
        Args:
            thread_id: Thread ID
            summary: Context summary
            
        Returns:
            Success status
        """
        thread = await self.get_thread(thread_id)
        if not thread:
            return False
        
        thread.context_summary = summary
        return await self.update_thread(thread)
    
    # Working Memory Management
    
    async def set_working_memory(self, 
                               key: str,
                               data: Dict[str, Any],
                               ttl: Optional[int] = None) -> bool:
        """
        Set data in working memory
        
        Args:
            key: Memory key
            data: Data to store
            ttl: Time to live in seconds
            
        Returns:
            Success status
        """
        memory_key = f"working_memory:{key}"
        ttl = ttl or self.working_memory_ttl
        
        if self._use_stub:
            self._stub_storage[memory_key] = {
                'data': data,
                'expires_at': datetime.utcnow() + timedelta(seconds=ttl)
            }
            return True
        
        try:
            await self.redis_client.setex(
                memory_key,
                ttl,
                json.dumps(data, default=str)
            )
            return True
        except Exception as e:
            logger.error(f"Failed to set working memory {key}: {e}")
            return False
    
    async def get_working_memory(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get data from working memory
        
        Args:
            key: Memory key
            
        Returns:
            Stored data or None
        """
        memory_key = f"working_memory:{key}"
        
        if self._use_stub:
            memory_data = self._stub_storage.get(memory_key)
            if memory_data:
                if datetime.utcnow() < memory_data['expires_at']:
                    return memory_data['data']
                else:
                    # Expired, remove it
                    del self._stub_storage[memory_key]
            return None
        
        try:
            data = await self.redis_client.get(memory_key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get working memory {key}: {e}")
            return None
    
    async def clear_working_memory(self, pattern: str = "*") -> int:
        """
        Clear working memory entries
        
        Args:
            pattern: Key pattern to match
            
        Returns:
            Number of keys cleared
        """
        if self._use_stub:
            keys_to_remove = []
            for key in self._stub_storage.keys():
                if key.startswith("working_memory:"):
                    if pattern == "*" or pattern in key:
                        keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self._stub_storage[key]
            
            return len(keys_to_remove)
        
        try:
            keys = await self.redis_client.keys(f"working_memory:{pattern}")
            if keys:
                await self.redis_client.delete(*keys)
                return len(keys)
            return 0
        except Exception as e:
            logger.error(f"Failed to clear working memory: {e}")
            return 0
    
    # Cross-Platform Threading
    
    async def link_cross_platform_thread(self, 
                                       primary_thread_id: str,
                                       platform: str,
                                       platform_thread_id: str) -> bool:
        """
        Link threads across platforms
        
        Args:
            primary_thread_id: Primary thread ID
            platform: Platform name
            platform_thread_id: Platform-specific thread ID
            
        Returns:
            Success status
        """
        link_key = f"cross_platform_link:{primary_thread_id}"
        
        # Get existing links
        existing_links = await self.get_working_memory(link_key) or {}
        existing_links[platform] = platform_thread_id
        
        return await self.set_working_memory(link_key, existing_links)
    
    async def get_cross_platform_links(self, 
                                     primary_thread_id: str) -> Dict[str, str]:
        """
        Get cross-platform thread links
        
        Args:
            primary_thread_id: Primary thread ID
            
        Returns:
            Platform links dictionary
        """
        link_key = f"cross_platform_link:{primary_thread_id}"
        return await self.get_working_memory(link_key) or {}
    
    # Cleanup and Maintenance
    
    async def cleanup_expired_threads(self) -> int:
        """
        Clean up expired conversation threads
        
        Returns:
            Number of threads cleaned up
        """
        if self._use_stub:
            # Clean up expired threads in stub storage
            now = datetime.utcnow()
            expired_keys = []
            
            for key, value in self._stub_storage.items():
                if key.startswith("thread:"):
                    try:
                        thread_data = ConversationThread.from_dict(value)
                        if thread_data.expires_at and now > thread_data.expires_at:
                            expired_keys.append(key)
                    except:
                        # Invalid data, remove it
                        expired_keys.append(key)
            
            for key in expired_keys:
                del self._stub_storage[key]
            
            return len(expired_keys)
        
        # For Redis implementation, expired keys are automatically cleaned up
        # due to TTL, but we could scan for any orphaned data here
        return 0
    
    async def get_thread_stats(self) -> Dict[str, Any]:
        """
        Get thread statistics
        
        Returns:
            Thread statistics
        """
        if self._use_stub:
            thread_keys = [k for k in self._stub_storage.keys() if k.startswith("thread:")]
            memory_keys = [k for k in self._stub_storage.keys() if k.startswith("working_memory:")]
            
            return {
                'total_threads': len(thread_keys),
                'working_memory_entries': len(memory_keys),
                'storage_type': 'stub',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        try:
            thread_keys = await self.redis_client.keys("thread:*")
            memory_keys = await self.redis_client.keys("working_memory:*")
            
            return {
                'total_threads': len(thread_keys),
                'working_memory_entries': len(memory_keys),
                'storage_type': 'redis',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get thread stats: {e}")
            return {}
    
    # Private helper methods
    
    async def _store_thread(self, thread: ConversationThread) -> bool:
        """Store thread in Redis or stub storage"""
        if self._use_stub:
            self._stub_storage[f"thread:{thread.id}"] = thread.to_dict()
            return True
        
        try:
            thread_data = json.dumps(thread.to_dict(), default=str)
            ttl = None
            if thread.expires_at:
                ttl = int((thread.expires_at - datetime.utcnow()).total_seconds())
                if ttl <= 0:
                    return False  # Already expired
            
            if ttl:
                await self.redis_client.setex(f"thread:{thread.id}", ttl, thread_data)
            else:
                await self.redis_client.set(f"thread:{thread.id}", thread_data)
            
            return True
        except Exception as e:
            logger.error(f"Failed to store thread {thread.id}: {e}")
            return False


# Factory function for easy integration
def create_redis_helper(config: Dict[str, Any] = None) -> RedisConversationHelper:
    """
    Create Redis conversation helper with configuration
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configured Redis helper instance
    """
    if config is None:
        config = {'use_stub': True}  # Default to stub mode for development
    
    return RedisConversationHelper(config)


# Utility functions for conversation management

async def create_twitter_thread(redis_helper: RedisConversationHelper,
                              tweet_id: str,
                              user_id: str,
                              initial_content: str) -> ConversationThread:
    """
    Create a Twitter conversation thread
    
    Args:
        redis_helper: Redis helper instance
        tweet_id: Twitter tweet ID
        user_id: Twitter user ID
        initial_content: Initial tweet content
        
    Returns:
        Created conversation thread
    """
    platform_data = {
        'tweet_id': tweet_id,
        'user_id': user_id,
        'platform': 'twitter'
    }
    
    thread = await redis_helper.create_thread(
        ThreadType.TWITTER,
        f"Twitter conversation - {tweet_id}",
        platform_data,
        [user_id]
    )
    
    # Add initial message
    await redis_helper.add_message(
        thread.id,
        MessageRole.USER,
        initial_content,
        'twitter',
        {'tweet_id': tweet_id}
    )
    
    return thread


async def create_maya_cerebras_conversation(redis_helper: RedisConversationHelper,
                                          session_id: str,
                                          context: Dict[str, Any]) -> ConversationThread:
    """
    Create a Maya-Cerebras conversation thread
    
    Args:
        redis_helper: Redis helper instance
        session_id: Session ID
        context: Conversation context
        
    Returns:
        Created conversation thread
    """
    platform_data = {
        'session_id': session_id,
        'context': context,
        'platform': 'maya_cerebras'
    }
    
    thread = await redis_helper.create_thread(
        ThreadType.MAYA_INTERNAL,
        f"Maya-Cerebras Session - {session_id}",
        platform_data,
        ['maya', 'cerebras']
    )
    
    return thread