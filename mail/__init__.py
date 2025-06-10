"""
Système de gestion des emails automatisé pour l'envoi de questions et l'évaluation des réponses
"""

from .send_questions import (
    send_question_from_api,
    send_daily_challenge_to_user,
    send_subject_challenge,
    test_api_connection
)

from .read_replies import (
    read_replies,
    get_unread_count
)

from .evaluate_responses import (
    evaluate_pending_responses,
    print_evaluation_report,
    get_evaluation_report
)

from .mail_system import (
    run_full_workflow,
    monitor_mode,
    send_question_to_student,
    send_questions_to_multiple_students
)

from .utils import (
    generate_question_id,
    load_conversations,
    save_conversations
)

__version__ = "1.0.0"
__author__ = "API-rhino Mail System" 