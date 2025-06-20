    from sqlmodel import SQLModel, Field
    from typing import Optional
    from datetime import datetime

    class User(SQLModel, table=True):
        id: Optional[int] = Field(default=None, primary_key=True)
        username: str
        email: str
        role: str
        subscriptions: Optional[str] = Field(default="", description="Liste des matières auxquelles l'utilisateur est abonné, séparées par des virgules")

    class Matiere(SQLModel, table=True):
        id: Optional[int] = Field(default=None, primary_key=True)
        name: str
        description: Optional[str] = None
        granularite: str = Field(default="semaine", description="jour|semaine|mois|2jours...")

    class Document(SQLModel, table=True):
        id: Optional[int] = Field(default=None, primary_key=True)
        file_hash: str = Field(unique=True, description="MD5 hash of the file content")
        filename: str
        matiere: str
        file_path: str = Field(description="Relative path from cours directory")
        document_type: str = Field(description="File extension without dot (md, pdf, etc.)")
        is_exam: bool = Field(default=False, description="Whether this document is an exam")
        file_size: int = Field(description="File size in bytes")
        upload_date: datetime = Field(default_factory=datetime.now, description="When the document was first added")
        last_modified: datetime = Field(default_factory=datetime.now, description="Last modification time of the file")
        last_indexed: Optional[datetime] = Field(default=None, description="When this document was last indexed in the vector database")
        is_indexed: bool = Field(default=False, description="Whether this document is currently in the vector index")

    class Challenge(SQLModel, table=True):
        id: Optional[int] = Field(default=None, primary_key=True)
        ref: Optional[str] = Field(default=None)  # ex: "SYD-001"
        question: str
        matiere: str
        date: str

    class ChallengeServed(SQLModel, table=True):
        id: Optional[int] = Field(default=None, primary_key=True)
        matiere: str
        granularite: str
        challenge_ref: str
        tick: int

    class LeaderboardEntry(SQLModel, table=True):
        id: Optional[int] = Field(default=None, primary_key=True)
        challenge_id: int
        user_id: int
        score: int
        rank: int

    class Token(SQLModel, table=True):
        id: Optional[int] = Field(default=None, primary_key=True)
        user_id: int
        token: str
        is_active: bool = True

    class StudentResponse(SQLModel, table=True):
        id: Optional[int] = Field(default=None, primary_key=True)
        question_id: str = Field(unique=True, description="L'ID unique de la question (ex: IDQ-20250610152017-f30548)")
        user_id: int = Field(foreign_key="user.id", description="ID de l'utilisateur")
        challenge_id: Optional[int] = Field(default=None, foreign_key="challenge.id", description="ID du challenge")
        response: Optional[str] = Field(default=None, description="Réponse de l'étudiant")
        response_date: Optional[str] = Field(default=None, description="Date de réponse de l'étudiant")
        sent_message_id: Optional[str] = Field(default=None, description="Message ID de l'email original")
        created_at: datetime = Field(default_factory=datetime.now, description="Date de création de l'enregistrement")
        updated_at: datetime = Field(default_factory=datetime.now, description="Date de dernière mise à jour")

    class Evaluation(SQLModel, table=True):
        id: Optional[int] = Field(default=None, primary_key=True)
        student_response_id: int = Field(foreign_key="studentresponse.id", description="ID de la réponse de l'étudiant")
        
        # Résultats principaux de l'évaluation
        score: Optional[int] = Field(default=None, description="Score obtenu")
        grade: Optional[str] = Field(default=None, description="Note sous forme de lettre (A, B, C, etc.)")
        feedback: Optional[str] = Field(default=None, description="Feedback général de l'évaluation")
        
        # Feedback détaillé (stocké en JSON)
        points_forts: Optional[str] = Field(default=None, description="Points forts identifiés (JSON array)")
        points_ameliorer: Optional[str] = Field(default=None, description="Points à améliorer (JSON array)")
        
        # Feedback envoyé
        feedback_sent: Optional[bool] = Field(default=False, description="Si le feedback a été envoyé à l'étudiant")
        feedback_sent_at: Optional[datetime] = Field(default=None, description="Date d'envoi du feedback")
        
        # Métadonnées de l'évaluation  
        evaluated_at: Optional[str] = Field(default=None, description="Date d'évaluation par l'API")
        raw_api_response: Optional[str] = Field(default=None, description="Réponse brute de l'API en JSON pour backup complet")
        
        created_at: datetime = Field(default_factory=datetime.now, description="Date de création de l'évaluation") 