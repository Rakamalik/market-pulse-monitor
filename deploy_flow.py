"""
Setup deployment untuk content_agent_pipeline - jadwal otomatis
menggantikan cron job manual.
"""

from content_pipeline_flow import content_agent_pipeline

if __name__ == "__main__":
    content_agent_pipeline.serve(
        name="daily-content-pipeline",
        cron="0 7 * * *",
        tags=["content-agent", "daily"]
    )
