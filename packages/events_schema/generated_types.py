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
    SETTING_CALL_REJECTED = "setting.call_rejected"
    SETTING_CALL_STARTED = "setting.call_started"
    SETTING_FOLLOWUP_SCHEDULED = "setting.followup_scheduled"
    SETTING_SALE_COMPLETED = "setting.sale_completed"
    SETTING_SALE_FAILED = "setting.sale_failed"
    SYSTEM_AGENT_OFFLINE = "system.agent_offline"
    SYSTEM_AGENT_ONLINE = "system.agent_online"
    SYSTEM_ERROR = "system.error"


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


class SettingCallRejectedPayload(BaseModel):
    lead_id: str
    reason: Optional[str] = None


class SettingCallStartedPayload(BaseModel):
    lead_id: str


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

