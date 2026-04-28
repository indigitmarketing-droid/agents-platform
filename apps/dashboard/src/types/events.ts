// Auto-generated event types. Do not edit manually.

export const EventTypes = {
  BUILDER_BLOG_PUBLISHED: "builder.blog_published" as const,
  BUILDER_BUILD_STARTED: "builder.build_started" as const,
  BUILDER_WEBSITE_READY: "builder.website_ready" as const,
  SCRAPING_BATCH_COMPLETED: "scraping.batch_completed" as const,
  SCRAPING_LEAD_FOUND: "scraping.lead_found" as const,
  SCRAPING_RUN_TARGET: "scraping.run_target" as const,
  SCRAPING_STARTED: "scraping.started" as const,
  SCRAPING_TRIGGER: "scraping.trigger" as const,
  SETTING_CALL_ACCEPTED: "setting.call_accepted" as const,
  SETTING_CALL_COMPLETED: "setting.call_completed" as const,
  SETTING_CALL_FAILED: "setting.call_failed" as const,
  SETTING_CALL_INITIATED: "setting.call_initiated" as const,
  SETTING_CALL_REJECTED: "setting.call_rejected" as const,
  SETTING_CALL_STARTED: "setting.call_started" as const,
  SETTING_CALL_UNCLEAR: "setting.call_unclear" as const,
  SETTING_FOLLOWUP_SCHEDULED: "setting.followup_scheduled" as const,
  SETTING_SALE_COMPLETED: "setting.sale_completed" as const,
  SETTING_SALE_FAILED: "setting.sale_failed" as const,
  SYSTEM_AGENT_OFFLINE: "system.agent_offline" as const,
  SYSTEM_AGENT_ONLINE: "system.agent_online" as const,
  SYSTEM_ERROR: "system.error" as const,
} as const;

export type EventType = (typeof EventTypes)[keyof typeof EventTypes];

export interface BuilderBlogPublishedPayload {
  lead_id: string;
  blog_url: string;
}

export interface BuilderBuildStartedPayload {
  lead_id: string;
}

export interface BuilderWebsiteReadyPayload {
  lead_id: string;
  site_url: string;
}

export interface ScrapingBatchCompletedPayload {
  total_found: number;
  batch_id: string;
}

export interface ScrapingLeadFoundPayload {
  lead: Record<string, unknown>;
}

export interface ScrapingRunTargetPayload {
  target_id: string;
}

export interface ScrapingStartedPayload {
  batch_id: string;
}

export interface ScrapingTriggerPayload {
  region?: string;
  batch_size?: number;
}

export interface SettingCallAcceptedPayload {
  lead_id: string;
  lead: Record<string, unknown>;
  call_brief?: Record<string, unknown>;
}

export interface SettingCallCompletedPayload {
  lead_id: string;
  conversation_id: string;
  transcript: string;
  duration_seconds?: number;
  audio_url?: string;
}

export interface SettingCallFailedPayload {
  lead_id: string;
  reason: string;
  call_sid?: string;
}

export interface SettingCallInitiatedPayload {
  lead_id: string;
  call_sid: string;
  call_type: string;
}

export interface SettingCallRejectedPayload {
  lead_id: string;
  reason?: string;
}

export interface SettingCallStartedPayload {
  lead_id: string;
}

export interface SettingCallUnclearPayload {
  lead_id: string;
  transcript_excerpt?: string;
}

export interface SettingFollowupScheduledPayload {
  lead_id: string;
  channel: string;
  scheduled_at: string;
}

export interface SettingSaleCompletedPayload {
  lead_id: string;
  amount: number;
}

export interface SettingSaleFailedPayload {
  lead_id: string;
  reason?: string;
}

export interface SystemAgentOfflinePayload {
  agent_id: string;
}

export interface SystemAgentOnlinePayload {
  agent_id: string;
}

export interface SystemErrorPayload {
  agent_id: string;
  error: string;
  event_id?: string;
}

export interface AgentEvent {
  id: string;
  type: EventType;
  source_agent: string;
  target_agent: string | null;
  payload: Record<string, unknown>;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'dead_letter';
  retry_count: number;
  created_at: string;
  processed_at: string | null;
  error: string | null;
}

export interface Agent {
  id: string;
  status: 'idle' | 'working' | 'error' | 'offline';
  last_heartbeat: string | null;
  current_task_id: string | null;
  metadata: Record<string, unknown>;
}
