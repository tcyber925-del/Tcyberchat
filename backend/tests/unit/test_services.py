"""
Unit tests for backend service layer validation
"""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

# Test basic service imports and instantiation
def test_service_imports():
    """Test that all services can be imported and instantiated"""
    from src.services.chat_service import get_chat_service
    from src.services.document_service import get_document_service
    from src.services.ai_service import get_ai_service
    from src.services.rag_service import get_rag_service

    # Test that services can be instantiated (FastAPI dependency injection pattern)
    chat_svc1 = get_chat_service()
    chat_svc2 = get_chat_service()
    assert chat_svc1 is not chat_svc2  # Different instances (dependency injection)

    doc_svc1 = get_document_service()
    doc_svc2 = get_document_service()
    assert doc_svc1 is not doc_svc2  # Different instances (dependency injection)

    # Test that services have required methods
    assert hasattr(chat_svc1, 'add_message')
    assert hasattr(chat_svc1, 'get_conversations')
    assert hasattr(doc_svc1, 'validate_file')
    assert hasattr(get_ai_service(), 'generate_response')
    assert hasattr(get_rag_service(), 'search_relevant_chunks')

def test_chat_service_basic():
    """Test basic ChatService functionality"""
    from src.services.chat_service import ChatService

    # Mock database
    mock_db = Mock(spec=Session)

    # Create service
    chat_service = ChatService(mock_db)

    # Test basic attributes
    assert chat_service.db == mock_db
    assert hasattr(chat_service, 'add_message')
    assert hasattr(chat_service, 'get_conversation_messages')

def test_document_service_validation():
    """Test DocumentService file validation"""
    from src.services.document_service import DocumentService

    # Mock database
    mock_db = Mock(spec=Session)

    # Create service
    doc_service = DocumentService(mock_db)

    # Test supported file types
    assert 'application/pdf' in doc_service.SUPPORTED_TEXT_TYPES
    assert 'image/jpeg' in doc_service.SUPPORTED_IMAGE_TYPES
    assert 'audio/mpeg' in doc_service.SUPPORTED_AUDIO_TYPES

    # Test file size limits
    assert doc_service.MAX_FILE_SIZE == 50 * 1024 * 1024  # 50MB
    assert doc_service.MAX_IMAGE_SIZE == 10 * 1024 * 1024  # 10MB
    assert doc_service.MAX_AUDIO_SIZE == 10 * 1024 * 1024  # 10MB

def test_ai_service_basic():
    """Test basic AIService functionality"""
    from src.services.ai_service import AIService

    ai_service = AIService()

    # Test basic attributes
    assert hasattr(ai_service, 'generate_response')
    assert hasattr(ai_service, 'generate_summary')
    assert hasattr(ai_service, 'embed_text')

def test_rag_service_basic():
    """Test basic RAGService functionality"""
    from src.services.rag_service import RAGService

    # Create service (will have limited functionality without LangChain)
    rag_service = RAGService()

    # Test basic attributes
    assert hasattr(rag_service, 'add_document_chunks')
    assert hasattr(rag_service, 'search_relevant_chunks')
    assert hasattr(rag_service, 'generate_rag_response')

def test_chat_service_add_message():
    """Test ChatService message addition"""
    from src.services.chat_service import ChatService

    # Mock database
    mock_db = Mock(spec=Session)

    # Mock conversation
    mock_conversation = Mock()
    mock_conversation.messages = []  # Empty list for messages
    mock_conversation.update_activity.return_value = None

    # Setup mocks
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = None
    mock_db.query.return_value.filter.return_value.first.return_value = mock_conversation

    chat_service = ChatService(mock_db)

    # Test message addition
    result = chat_service.add_message("conv-id", "Hello", "user")

    # Verify database operations were called
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()

    # Verify result is a Message object with correct data
    assert result is not None
    assert hasattr(result, 'conversation_id')
    assert hasattr(result, 'content')
    assert hasattr(result, 'type')

def test_document_service_validate_file():
    """Test DocumentService file validation"""
    from src.services.document_service import DocumentService

    mock_db = Mock(spec=Session)
    doc_service = DocumentService(mock_db)

    # Mock file
    mock_file = Mock()
    mock_file.filename = "test.pdf"
    mock_file.content_type = "application/pdf"
    mock_file.size = 1024  # Small file

    # Test valid file
    is_valid, error_msg = doc_service.validate_file(mock_file)
    assert is_valid is True
    assert error_msg is None

    # Test invalid file type
    mock_file.content_type = "application/exe"
    is_valid, error_msg = doc_service.validate_file(mock_file)
    assert is_valid is False
    assert "Unsupported file type" in error_msg

def test_document_service_file_size_limits():
    """Test DocumentService file size validation"""
    from src.services.document_service import DocumentService

    mock_db = Mock(spec=Session)
    doc_service = DocumentService(mock_db)

    # Mock oversized file
    mock_file = Mock()
    mock_file.filename = "large.pdf"
    mock_file.content_type = "application/pdf"
    mock_file.size = 100 * 1024 * 1024  # 100MB

    is_valid, error_msg = doc_service.validate_file(mock_file)
    assert is_valid is False
    assert "File too large" in error_msg

if __name__ == "__main__":
    # Run basic tests
    test_service_imports()
    test_chat_service_basic()
    test_document_service_validation()
    test_ai_service_basic()
    test_rag_service_basic()
    test_chat_service_add_message()
    test_document_service_validate_file()
    test_document_service_file_size_limits()

    print("All basic unit tests passed!")