from .database import Base
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

class Job(Base):
    __tablename__ = "bigdata_recruit_job"

    id = Column(Integer, primary_key=True, index=True)

    job_name = Column(String, index=True)
    company_name = Column(String, index=True)
    job_salary = Column(String)

    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)

    industry_name = Column(String)
    industry_list = Column(JSON, nullable=True)

    work_city = Column(String, index=True)
    city_district = Column(String)
    street_name = Column(String)

    work_major = Column(String, index=True)
    work_type = Column(String)
    your_education = Column(String)
    working_exp = Column(String)
    company_size = Column(String)

    job_summary = Column(Text)
    job_summary_cut = Column(Text)
    job_summary_cut_filtered = Column(Text)

    company_benefits = Column(Text)
    company_benefits_cut = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        data = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        
        # 安全处理 created_at
        if data.get("created_at") is not None:
            try:
                # 如果已经是 datetime 对象
                if hasattr(data["created_at"], 'strftime'):
                    data["created_at"] = data["created_at"].strftime("%Y-%m-%d %H:%M:%S")
                elif isinstance(data["created_at"], str):
                    # 如果是字符串，尝试解析
                    from datetime import datetime
                    dt_str = data["created_at"]
                    # 处理各种格式
                    dt_str = dt_str.replace('Z', '+00:00')
                    if 'T' in dt_str:
                        dt = datetime.fromisoformat(dt_str)
                    else:
                        # 如果是 "2024-01-01 00:00:00" 格式
                        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                    data["created_at"] = dt.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    # 其他类型，直接转字符串
                    data["created_at"] = str(data["created_at"])
            except Exception as e:
                # 如果解析失败，设为当前时间
                from datetime import datetime
                data["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            # 如果是 None，设为当前时间
            from datetime import datetime
            data["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return data


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    resume_analyses = relationship("ResumeAnalysis", back_populates="user", cascade="all, delete-orphan")
    matching_histories = relationship("MatchingHistory", back_populates="user", cascade="all, delete-orphan")
    interview_records = relationship("InterviewRecord", back_populates="user", cascade="all, delete-orphan")
    favorite_jobs = relationship("FavoriteJob", back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True, nullable=False)

    real_name = Column(String(50), nullable=True)
    phone = Column(String(20), nullable=True)
    gender = Column(String(10), nullable=True)
    birth_year = Column(Integer, nullable=True)
    location = Column(String(100), nullable=True)

    school = Column(String(100), nullable=True)
    major = Column(String(100), nullable=True)
    degree = Column(String(20), nullable=True)
    graduation_year = Column(Integer, nullable=True)

    target_position = Column(String(200), nullable=True)
    target_city = Column(String(200), nullable=True)
    expected_salary_min = Column(Integer, nullable=True)
    expected_salary_max = Column(Integer, nullable=True)
    work_experience = Column(String(20), nullable=True)

    tech_skills = Column(Text, nullable=True)
    about_me = Column(Text, nullable=True)

    is_profile_complete = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")


class ResumeAnalysis(Base):
    __tablename__ = "resume_analyses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=True)
    overall_score = Column(Float, nullable=True)
    overall_rating = Column(String(50), nullable=True)
    char_count = Column(Integer, nullable=True)
    elapsed_seconds = Column(Float, nullable=True)
    result_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="resume_analyses")


class MatchingHistory(Base):
    __tablename__ = "matching_histories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    mode = Column(String(20), nullable=False)
    filename = Column(String(255), nullable=True)
    resume_preview = Column(Text, nullable=True)
    match_score = Column(Float, nullable=True)
    job_name = Column(String(255), nullable=True)
    company_name = Column(String(255), nullable=True)
    top_k = Column(Integer, nullable=True)
    result_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="matching_histories")


class InterviewRecord(Base):
    __tablename__ = "interview_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(String(100), nullable=True, index=True)
    style = Column(String(50), nullable=True)
    style_name = Column(String(50), nullable=True)
    job_name = Column(String(255), nullable=True)
    turns = Column(Integer, default=0)
    duration_seconds = Column(Integer, nullable=True)
    history_json = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="interview_records")


class FavoriteJob(Base):
    __tablename__ = "favorite_jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("bigdata_recruit_job.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="favorite_jobs")
    job = relationship("Job")


class JobTopic(Base):
    __tablename__ = "job_topics"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    keywords_json = Column(Text, nullable=True)
    job_count = Column(Integer, default=0)
    centroid_json = Column(Text, nullable=True)
    positions = Column(Text, nullable=True)
    skills_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    relations = relationship("JobTopicRelation", back_populates="topic", cascade="all, delete-orphan")


class JobTopicRelation(Base):
    __tablename__ = "job_topic_relation"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("bigdata_recruit_job.id"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("job_topics.id"), nullable=False, index=True)
    confidence = Column(Float, default=1.0)

    topic = relationship("JobTopic", back_populates="relations")
    job = relationship("Job")


class JobSkillRelation(Base):
    __tablename__ = "job_skill_relation"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("bigdata_recruit_job.id"), nullable=False, index=True)
    topic_id = Column(Integer, ForeignKey("job_topics.id"), nullable=True, index=True)
    job_name = Column(String(255), nullable=True, index=True)
    raw_job_name = Column(String(255), nullable=True)
    skill = Column(String(100), nullable=False, index=True)
    tier = Column(String(20), nullable=True)
    is_emerging = Column(Boolean, default=False)
    weight = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("Job")
    topic = relationship("JobTopic")