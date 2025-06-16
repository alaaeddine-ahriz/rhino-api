import json
from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import Session, select
from app.db.session import engine
from app.db.models import StudentResponse, Evaluation, User, Challenge

class StudentResponseService:
    """Service pour gérer les réponses étudiantes en base de données."""
    
    def find_or_create_user(self, session: Session, email: str, user_id: int = None) -> int:
        """Trouve ou crée un utilisateur."""
        if user_id:
            user = session.get(User, user_id)
            if user:
                return user.id
        
        # Chercher par email
        stmt = select(User).where(User.email == email)
        user = session.exec(stmt).first()
        if user:
            return user.id
        
        # Créer un nouvel utilisateur
        new_user = User(
            username=email.split('@')[0],
            email=email,
            role="student"
        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        return new_user.id
    
    def find_challenge_by_api_id(self, session: Session, api_challenge_id: int) -> Optional[int]:
        """Trouve un challenge par son api_challenge_id."""
        if not api_challenge_id:
            return None
        
        challenge = session.get(Challenge, api_challenge_id)
        return challenge.id if challenge else None
    
    def save_question(self, question_id: str, student_email: str, user_id: int = None, 
                     api_challenge_id: int = None, sent_message_id: str = None) -> bool:
        """Sauvegarde une question posée à un étudiant."""
        try:
            with Session(engine) as session:
                # Vérifier si existe déjà
                stmt = select(StudentResponse).where(StudentResponse.question_id == question_id)
                existing = session.exec(stmt).first()
                if existing:
                    return True
                
                # Trouver ou créer l'utilisateur
                user_id = self.find_or_create_user(session, student_email, user_id)
                
                # Trouver le challenge
                challenge_id = self.find_challenge_by_api_id(session, api_challenge_id)
                
                # Créer la réponse (sans réponse pour l'instant)
                student_response = StudentResponse(
                    question_id=question_id,
                    user_id=user_id,
                    challenge_id=challenge_id,
                    response=None,
                    response_date=None,
                    sent_message_id=sent_message_id,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                session.add(student_response)
                session.commit()
                return True
                
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde de la question: {e}")
            return False
    
    def save_response(self, question_id: str, response: str, response_date: str = None, 
                     response_from: str = None) -> bool:
        """Sauvegarde la réponse d'un étudiant."""
        try:
            with Session(engine) as session:
                # Trouver la réponse existante
                stmt = select(StudentResponse).where(StudentResponse.question_id == question_id)
                student_response = session.exec(stmt).first()
                
                if not student_response:
                    print(f"❌ Question {question_id} non trouvée pour sauvegarder la réponse")
                    return False
                
                # Mettre à jour la réponse
                student_response.response = response
                student_response.response_date = response_date or datetime.now().isoformat()
                student_response.updated_at = datetime.now()
                
                session.add(student_response)
                session.commit()
                return True
                
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde de la réponse: {e}")
            return False
    
    def save_evaluation(self, question_id: str, evaluation_data: Dict[str, Any]) -> bool:
        """Sauvegarde l'évaluation d'une réponse."""
        try:
            with Session(engine) as session:
                # Trouver la réponse
                stmt = select(StudentResponse).where(StudentResponse.question_id == question_id)
                student_response = session.exec(stmt).first()
                
                if not student_response:
                    print(f"❌ Question {question_id} non trouvée pour sauvegarder l'évaluation")
                    return False
                
                # Vérifier si évaluation existe déjà
                stmt = select(Evaluation).where(Evaluation.student_response_id == student_response.id)
                existing_eval = session.exec(stmt).first()
                
                if existing_eval:
                    # Mettre à jour l'évaluation existante
                    self._update_evaluation(existing_eval, evaluation_data)
                    session.add(existing_eval)
                else:
                    # Créer nouvelle évaluation
                    evaluation = self._create_evaluation(student_response.id, evaluation_data)
                    session.add(evaluation)
                
                session.commit()
                return True
                
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde de l'évaluation: {e}")
            return False
    
    def _create_evaluation(self, student_response_id: int, evaluation_data: Dict[str, Any]) -> Evaluation:
        """Crée un objet Evaluation à partir des données."""
        # Gérer les différents formats d'évaluation
        if 'raw_api_response' in evaluation_data:
            # Format avec raw_api_response
            api_data = evaluation_data['raw_api_response'].get('data', {})
            score = api_data.get('score', evaluation_data.get('score'))
            feedback = api_data.get('feedback', evaluation_data.get('feedback'))
            points_forts = json.dumps(api_data.get('points_forts', []))
            points_ameliorer = json.dumps(api_data.get('points_ameliorer', []))
            evaluated_at = api_data.get('evaluated_at')
            raw_response = json.dumps(evaluation_data['raw_api_response'])
        else:
            # Format simple
            score = evaluation_data.get('score')
            feedback = evaluation_data.get('feedback')
            if isinstance(feedback, list):
                feedback = json.dumps(feedback)
            points_forts = None
            points_ameliorer = None
            evaluated_at = None
            raw_response = json.dumps(evaluation_data)
        
        return Evaluation(
            student_response_id=student_response_id,
            score=score,
            grade=evaluation_data.get('grade'),
            feedback=feedback,
            points_forts=points_forts,
            points_ameliorer=points_ameliorer,
            feedback_sent=False,
            evaluated_at=evaluated_at,
            raw_api_response=raw_response,
            created_at=datetime.now()
        )
    
    def _update_evaluation(self, evaluation: Evaluation, evaluation_data: Dict[str, Any]):
        """Met à jour un objet Evaluation existant."""
        # Gérer les différents formats d'évaluation
        if 'raw_api_response' in evaluation_data:
            api_data = evaluation_data['raw_api_response'].get('data', {})
            evaluation.score = api_data.get('score', evaluation_data.get('score'))
            evaluation.feedback = api_data.get('feedback', evaluation_data.get('feedback'))
            evaluation.points_forts = json.dumps(api_data.get('points_forts', []))
            evaluation.points_ameliorer = json.dumps(api_data.get('points_ameliorer', []))
            evaluation.evaluated_at = api_data.get('evaluated_at')
            evaluation.raw_api_response = json.dumps(evaluation_data['raw_api_response'])
        else:
            evaluation.score = evaluation_data.get('score')
            feedback = evaluation_data.get('feedback')
            if isinstance(feedback, list):
                feedback = json.dumps(feedback)
            evaluation.feedback = feedback
            evaluation.raw_api_response = json.dumps(evaluation_data)
        
        evaluation.grade = evaluation_data.get('grade')
    
    def mark_feedback_sent(self, question_id: str, sent_to: str = None) -> bool:
        """Marque le feedback comme envoyé."""
        try:
            with Session(engine) as session:
                # Trouver la réponse et son évaluation
                stmt = (
                    select(StudentResponse, Evaluation)
                    .join(Evaluation)
                    .where(StudentResponse.question_id == question_id)
                )
                result = session.exec(stmt).first()
                
                if not result:
                    print(f"❌ Question {question_id} ou évaluation non trouvée")
                    return False
                
                student_response, evaluation = result
                evaluation.feedback_sent = True
                evaluation.feedback_sent_at = datetime.now()
                
                session.add(evaluation)
                session.commit()
                return True
                
        except Exception as e:
            print(f"❌ Erreur lors du marquage du feedback: {e}")
            return False
    
    def get_student_response(self, question_id: str) -> Optional[Dict[str, Any]]:
        """Récupère une réponse étudiant avec ses détails."""
        try:
            with Session(engine) as session:
                stmt = (
                    select(StudentResponse, User, Challenge, Evaluation)
                    .join(User, StudentResponse.user_id == User.id)
                    .outerjoin(Challenge, StudentResponse.challenge_id == Challenge.id)
                    .outerjoin(Evaluation, Evaluation.student_response_id == StudentResponse.id)
                    .where(StudentResponse.question_id == question_id)
                )
                result = session.exec(stmt).first()
                
                if not result:
                    return None
                
                student_response, user, challenge, evaluation = result
                
                # Construire la réponse
                response_data = {
                    'question_id': student_response.question_id,
                    'student_email': user.email,
                    'user_id': user.id,
                    'question': challenge.question if challenge else None,
                    'matiere': challenge.matiere if challenge else None,
                    'challenge_ref': challenge.ref if challenge else None,
                    'response': student_response.response,
                    'response_date': student_response.response_date,
                    'evaluated': evaluation is not None,
                    'created_at': student_response.created_at.isoformat(),
                    'updated_at': student_response.updated_at.isoformat()
                }
                
                if evaluation:
                    response_data['evaluation'] = {
                        'score': evaluation.score,
                        'grade': evaluation.grade,
                        'feedback': evaluation.feedback,
                        'points_forts': json.loads(evaluation.points_forts) if evaluation.points_forts else None,
                        'points_ameliorer': json.loads(evaluation.points_ameliorer) if evaluation.points_ameliorer else None,
                        'feedback_sent': evaluation.feedback_sent,
                        'feedback_sent_at': evaluation.feedback_sent_at.isoformat() if evaluation.feedback_sent_at else None,
                        'evaluated_at': evaluation.evaluated_at,
                        'created_at': evaluation.created_at.isoformat()
                    }
                
                return response_data
                
        except Exception as e:
            print(f"❌ Erreur lors de la récupération: {e}")
            return None
    
    def get_all_responses(self) -> Dict[str, Any]:
        """Récupère toutes les réponses au format conversations.json."""
        try:
            with Session(engine) as session:
                stmt = (
                    select(StudentResponse, User, Challenge, Evaluation)
                    .join(User, StudentResponse.user_id == User.id)
                    .outerjoin(Challenge, StudentResponse.challenge_id == Challenge.id)
                    .outerjoin(Evaluation, Evaluation.student_response_id == StudentResponse.id)
                )
                results = session.exec(stmt).all()
                
                conversations = {}
                for student_response, user, challenge, evaluation in results:
                    response_data = {
                        'student': user.email,
                        'question': challenge.question if challenge else '',
                        'response': student_response.response,
                        'evaluated': evaluation is not None,
                        'user_id': user.id,
                        'response_date': student_response.response_date,
                        'response_from': user.email
                    }
                    
                    if challenge:
                        response_data.update({
                            'matiere': challenge.matiere,
                            'challenge_ref': challenge.ref,
                            'api_challenge_id': challenge.id
                        })
                    
                    if evaluation:
                        eval_data = {
                            'score': evaluation.score,
                            'grade': evaluation.grade,
                            'feedback': evaluation.feedback
                        }
                        
                        if evaluation.points_forts:
                            eval_data['points_forts'] = json.loads(evaluation.points_forts)
                        if evaluation.points_ameliorer:
                            eval_data['points_ameliorer'] = json.loads(evaluation.points_ameliorer)
                        
                        response_data['evaluation'] = eval_data
                        
                        if evaluation.feedback_sent:
                            response_data['feedback_sent'] = True
                            response_data['feedback_sent_to'] = user.email
                    
                    conversations[student_response.question_id] = response_data
                
                return conversations
                
        except Exception as e:
            print(f"❌ Erreur lors de la récupération de toutes les réponses: {e}")
            return {}
    
    def question_exists(self, question_id: str) -> bool:
        """Vérifie si une question existe dans la base."""
        try:
            with Session(engine) as session:
                stmt = select(StudentResponse).where(StudentResponse.question_id == question_id)
                result = session.exec(stmt).first()
                return result is not None
        except Exception as e:
            print(f"❌ Erreur lors de la vérification: {e}")
            return False 