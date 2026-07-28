from django.core.mail import get_connection


def smtp_connection_for_company(company, *, timeout=10):
    return get_connection(
        host=company.smtp_host,
        port=company.smtp_port,
        username=company.smtp_username,
        password=company.smtp_app_key,
        use_tls=company.smtp_use_tls,
        use_ssl=company.smtp_port == 465 and not company.smtp_use_tls,
        timeout=timeout,
    )
