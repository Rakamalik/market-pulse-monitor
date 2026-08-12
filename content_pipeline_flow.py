"""
Content Agent Pipeline - Prefect Flow
"""

from prefect import flow, task
import json


@task(retries=2, retry_delay_seconds=30, log_prints=True)
def stage1_discover_trends():
    from trend_finder import discover_trends
    topics = discover_trends(limit=10)
    print(f"Stage 1 selesai: {len(topics)} topik ditemukan")
    return topics


@task(retries=1, retry_delay_seconds=60, log_prints=True)
def stage2_financial_angle(topics):
    from financial_angle_finder import process_topics
    results = process_topics(topics, max_topics=5)
    print(f"Stage 2 selesai: {len(results)} topik dianalisis")
    return results


@task(retries=1, retry_delay_seconds=15, log_prints=True)
def stage3_validate_enrich(stage2_results):
    from validate_and_draft import enrich_analysis
    drafts = enrich_analysis(stage2_results)
    print(f"Stage 3+4 selesai: {len(drafts)} draft tervalidasi")

    with open('drafts_output.json', 'w', encoding='utf-8') as f:
        json.dump(drafts, f, indent=2, ensure_ascii=False)

    return drafts


@task(retries=2, retry_delay_seconds=10, log_prints=True)
def stage4_notify(drafts):
    from validate_and_draft import send_telegram_notification
    send_telegram_notification(drafts)
    print("Notifikasi terkirim")


@flow(name="content-agent-pipeline", log_prints=True)
def content_agent_pipeline():
    topics = stage1_discover_trends()
    stage2_results = stage2_financial_angle(topics)
    drafts = stage3_validate_enrich(stage2_results)
    stage4_notify(drafts)

    print(f"Pipeline selesai: {len(drafts)} draft dihasilkan")
    return drafts


if __name__ == "__main__":
    content_agent_pipeline()
