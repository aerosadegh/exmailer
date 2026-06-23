# Advanced Features
## Dynamic Variable Interpolation
ExMailer supports `f-string` style placeholders in your email body or template.

```Python
emailer.send_email(
    subject="System Alert",
    body="Node {node_id} reported status: {status}",
    recipients=["admin@company.com"],
    template_vars={"node_id": "SRV-01", "status": "CRITICAL"}
)
```
## Custom Template Engine
You can define high-fidelity HTML templates with CSS and register them for reuse.

Define the Template: Use `{body}` as the placeholder for the email content.

Register: Use `register_custom_template`.


Execute: Reference the template by name in `send_email`.
