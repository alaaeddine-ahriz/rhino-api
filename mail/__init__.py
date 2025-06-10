"""
Mail System - Essential email functionality for challenge distribution

This module provides the core functionality for sending challenge emails
to students and tracking conversations.
"""

from .send_questions import send_question_from_api, get_challenge_from_api
from .database_utils import get_student_by_id, get_all_students, get_students_by_subscription
from .utils import generate_question_id, load_conversations, save_conversations
from .email_reader import wait_for_reply, display_reply, read_new_replies
from .evaluator import evaluate_and_display, evaluate_response_simple, send_feedback_email, evaluate_display_and_send_feedback

__all__ = [
    'send_question_from_api',
    'get_challenge_from_api', 
    'get_student_by_id',
    'get_all_students',
    'get_students_by_subscription',
    'generate_question_id',
    'load_conversations',
    'save_conversations',
    'wait_for_reply',
    'display_reply',
    'read_new_replies',
    'evaluate_and_display',
    'evaluate_response_simple',
    'send_feedback_email',
    'evaluate_display_and_send_feedback'
]

__version__ = "1.0.0"
__author__ = "Le Rhino Team" 