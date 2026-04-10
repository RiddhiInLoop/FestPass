import pytest
from unittest.mock import patch, MagicMock
import validators
import event_backend

def test_email_validation():
    assert validators.is_valid_email("test@despu.edu.in") == True
    assert validators.is_valid_email("user.name+tag@despu.edu.in") == True
    assert validators.is_valid_email("invalid-email") == False
    assert validators.is_valid_email("test@example.com") == False
    assert validators.is_valid_email("") == False # Now required

def test_seat_validation():
    assert validators.is_valid_seat("A1") == True
    assert validators.is_valid_seat("VIP-100") == True
    assert validators.is_valid_seat("1234567890") == True
    assert validators.is_valid_seat("12345678901") == False # > 10 chars
    assert validators.is_valid_seat("") == False
    assert validators.is_valid_seat("Seat @1") == False # Special chars

@patch('event_backend.save_ticket')
def test_pass_image_generation(mock_save_ticket):
    # Mock save_ticket to skip DB operations during this test
    mock_save_ticket.return_value = None
    
    img, ticket_id = event_backend.generate_pass_image(
        name="John Doe", 
        dept="Computer Science", 
        event="Hackathon", 
        seat="A1", 
        email="john@despu.edu.in", 
        roll_no="CS101",
        theme_name="Tech",
        email_verified=True
    )
    
    # Verify dimensions
    assert img.size == (900, 550)
    
    # Verify Ticket ID properties
    assert isinstance(ticket_id, str)
    assert ticket_id.isupper()
    assert len(ticket_id) > 0
    assert "-" not in ticket_id # uuid generated format

    # Ensure save_ticket was called with correct arguments
    mock_save_ticket.assert_called_once_with(ticket_id, "John Doe", "Computer Science", "Hackathon", "A1", "john@despu.edu.in", "CS101", True)
