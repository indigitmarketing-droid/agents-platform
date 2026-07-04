"""Auto-generated event types. Do not edit manually."""
from pydantic import BaseModel
from typing import Optional


# Event type constants
class EventTypes:
    BUILDER_BLOG_PUBLISHED = "builder.blog_published"
    BUILDER_BUILD_STARTED = "builder.build_started"
    BUILDER_WEBSITE_READY = "builder.website_ready"
    SCRAPING_BATCH_COMPLETED = "scraping.batch_completed"
    SCRAPING_LEAD_FOUND = "scraping.lead_found"
    SCRAPING_RUN_TARGET = "scraping.run_target"
    SCRAPING_STARTED = "scraping.started"
    SCRAPING_TRIGGER = "scraping.trigger"
    SETTING_CALL_ACCEPTED = "setting.call_accepted"
    SETTING_CALL_COMPLETED = "setting.call_completed"
    SETTING_CALL_FAILED = "setting.call_failed"
    SETTING_CALL_INITIATED = "setting.call_initiated"
    SETTING_CALL_REJECTED = "setting.call_rejected"
    SETTING_CALL_STARTED = "setting.call_started"
    SETTING_CALL_UNCLEAR = "setting.call_unclear"
    SETTING_FOLLOWUP_SCHEDULED = "setting.followup_scheduled"
    SETTING_SALE_COMPLETED = "setting.sale_completed"
    SETTING_SALE_FAILED = "setting.sale_failed"
    SYSTEM_AGENT_OFFLINE = "system.agent_offline"
    SYSTEM_AGENT_ONLINE = "system.agent_online"
    SYSTEM_ERROR = "system.error"
    VIDEO_EDIT_REQUESTED = "video.edit_requested"
    VIDEO_FAILED = "video.failed"
    VIDEO_GENERATE_REQUESTED = "video.generate_requested"
    VIDEO_PROCESSING_STARTED = "video.processing_started"
    VIDEO_READY = "video.ready"


class BuilderBlogPublishedPayload(BaseModel):
    lead_id: str
    blog_url: str


class BuilderBuildStartedPayload(BaseModel):
    lead_id: str


class BuilderWebsiteReadyPayload(BaseModel):
    lead_id: str
    site_url: str


class ScrapingBatchCompletedPayload(BaseModel):
    total_found: int
    batch_id: str


class ScrapingLeadFoundPayload(BaseModel):
    lead: dict


class ScrapingRunTargetPayload(BaseModel):
    target_id: str


class ScrapingStartedPayload(BaseModel):
    batch_id: str


class ScrapingTriggerPayload(BaseModel):
    region: Optional[str] = None
    batch_size: Optional[int] = None


class SettingCallAcceptedPayload(BaseModel):
    lead_id: str
    lead: dict
    call_brief: Optional[dict] = None


class SettingCallCompletedPayload(BaseModel):
    lead_id: str
    conversation_id: str
    transcript: str
    duration_seconds: Optional[int] = None
    audio_url: Optional[str] = None


class SettingCallFailedPayload(BaseModel):
    lead_id: str
    reason: str
    call_sid: Optional[str] = None


class SettingCallInitiatedPayload(BaseModel):
    lead_id: str
    call_sid: str
    call_type: str


class SettingCallRejectedPayload(BaseModel):
    lead_id: str
    reason: Optional[str] = None


class SettingCallStartedPayload(BaseModel):
    lead_id: str


class SettingCallUnclearPayload(BaseModel):
    lead_id: str
    transcript_excerpt: Optional[str] = None


class SettingFollowupScheduledPayload(BaseModel):
    lead_id: str
    channel: str
    scheduled_at: str


class SettingSaleCompletedPayload(BaseModel):
    lead_id: str
    amount: float


class SettingSaleFailedPayload(BaseModel):
    lead_id: str
    reason: Optional[str] = None


class SystemAgentOfflinePayload(BaseModel):
    agent_id: str


class SystemAgentOnlinePayload(BaseModel):
    agent_id: str


class SystemErrorPayload(BaseModel):
    agent_id: str
    error: str
    event_id: Optional[str] = None


class VideoEditRequestedPayload(BaseModel):
    job_id: Optional[str] = None
    operation: str
    params: Optional[dict] = None
    input_path: Optional[str] = None
    input_paths: Optional[list] = None
    output_path: Optional[str] = None
    reply_to: Optional[str] = None


class VideoFailedPayload(BaseModel):
    job_id: Optional[str] = None
    error: str


class VideoGenerateRequestedPayload(BaseModel):
    job_id: Optional[str] = None
    template: Optional[str] = None
    images: list
    audio: Optional[str] = None
    options: Optional[dict] = None
    output_path: Optional[str] = None
    reply_to: Optional[str] = None


class VideoProcessingStartedPayload(BaseModel):
    job_id: str


class VideoReadyPayload(BaseModel):
    job_id: Optional[str] = None
    output_path: str
    operation: Optional[str] = None
    template: Optional[str] = None
    metadata: Optional[dict] = None

