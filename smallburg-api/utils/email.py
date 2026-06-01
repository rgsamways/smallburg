import resend
import logging

logger = logging.getLogger(__name__)


def _send(to: str, subject: str, html: str) -> bool:
    try:
        resend.Emails.send({
            "from": "noreply@smallburg.ca",
            "to": to,
            "subject": subject,
            "html": html,
        })
        return True
    except Exception as e:
        logger.error(f"Resend error sending to {to}: {e}")
        return False


def send_claim_notification(
    operator_email: str,
    claim_email: str,
    postal: str,
    municipality: str,
    workspace_id: str,
    slug: str,
    claim_id: str,
    requested_at: str,
) -> bool:
    subject = f"Workspace claim request — {municipality}"
    html = f"""
    <div style="font-family:monospace;max-width:540px;margin:0 auto;background:#0f0e0b;color:#e8e4dc;padding:32px;border-radius:8px;">
      <p style="color:#c8a96e;font-size:11px;letter-spacing:0.1em;text-transform:uppercase;margin:0 0 24px">Smallburg · Claim Request</p>
      <h2 style="font-size:18px;margin:0 0 24px;font-weight:500">{municipality}</h2>
      <table style="width:100%;border-collapse:collapse;font-size:13px;">
        <tr><td style="padding:6px 0;color:#888;width:140px">Email</td><td>{claim_email}</td></tr>
        <tr><td style="padding:6px 0;color:#888">Postal</td><td>{postal}</td></tr>
        <tr><td style="padding:6px 0;color:#888">Workspace</td><td>{workspace_id} / {slug}</td></tr>
        <tr><td style="padding:6px 0;color:#888">Requested</td><td>{requested_at}</td></tr>
        <tr><td style="padding:6px 0;color:#888">Claim ID</td><td style="font-family:monospace">{claim_id}</td></tr>
      </table>
      <p style="margin:32px 0 8px;font-size:12px;color:#888">To grant access:</p>
      <pre style="background:#1a1917;padding:12px;border-radius:4px;font-size:12px;color:#c8a96e;overflow-x:auto">curl -X POST https://api.smallburg.ca/api/claims/{claim_id}/grant \\
  -H "X-Operator-Key: YOUR_OPERATOR_KEY"</pre>
      <p style="margin-top:32px;font-size:11px;color:#555">Smallburg · smallburg.ca</p>
    </div>
    """
    return _send(operator_email, subject, html)


def send_magic_link(
    claimant_email: str,
    municipality: str,
    magic_link_url: str,
    expiry_hours: int = 24,
) -> bool:
    subject = f"Your Smallburg workspace is ready — {municipality}"
    html = f"""
    <div style="font-family:sans-serif;max-width:520px;margin:0 auto;background:#0f0e0b;color:#e8e4dc;padding:40px;border-radius:8px;">
      <p style="color:#c8a96e;font-size:11px;letter-spacing:0.1em;text-transform:uppercase;margin:0 0 32px">Smallburg</p>
      <h2 style="font-size:22px;font-weight:400;margin:0 0 16px">Your workspace is ready.</h2>
      <p style="color:#aaa;font-size:14px;line-height:1.6;margin:0 0 32px">
        You've been granted access to the <strong style="color:#e8e4dc">{municipality}</strong> workspace on Smallburg.
        Click below to complete your account setup. This link expires in {expiry_hours} hours.
      </p>
      <a href="{magic_link_url}"
         style="display:inline-block;background:#c8a96e;color:#0f0e0b;padding:14px 28px;border-radius:4px;text-decoration:none;font-size:14px;font-weight:600;letter-spacing:0.02em;">
        Set up my account →
      </a>
      <p style="margin-top:32px;font-size:12px;color:#555">
        Or copy: <span style="color:#888">{magic_link_url}</span>
      </p>
      <hr style="border:none;border-top:1px solid #222;margin:40px 0 24px">
      <p style="font-size:11px;color:#444">Smallburg · Built near Bancroft, Ontario · smallburg.ca</p>
    </div>
    """
    return _send(claimant_email, subject, html)
