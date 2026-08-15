"""Render scored deals into a simple, readable HTML report."""

import datetime


def render_html_report(deals: list) -> str:
    today = datetime.date.today().strftime("%B %d, %Y")

    if not deals:
        rows_html = "<tr><td colspan='5' style='padding:24px;text-align:center;color:#666;'>No deals cleared the profit bar today.</td></tr>"
    else:
        rows_html = ""
        for d in deals:
            rows_html += f"""
            <tr>
                <td><a href="{d.listing_url}" target="_blank">{d.title}</a></td>
                <td>${d.buy_price:,.2f}</td>
                <td>${d.est_resale_price:,.2f}</td>
                <td style="color:#1a7f37;font-weight:600;">${d.net_profit:,.2f}</td>
                <td>{d.margin_pct:.1f}%</td>
            </tr>"""

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Daily Card Flip Report — {today}</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; background:#f7f7f8; margin:0; padding:32px; color:#1a1a1a; }}
  .wrap {{ max-width: 860px; margin: 0 auto; background:#fff; border-radius:12px; padding:32px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
  h1 {{ font-size:20px; margin:0 0 4px; }}
  .sub {{ color:#666; font-size:13px; margin-bottom:24px; }}
  table {{ width:100%; border-collapse: collapse; font-size:14px; }}
  th {{ text-align:left; padding:10px 12px; border-bottom:2px solid #eee; color:#666; font-weight:600; font-size:12px; text-transform:uppercase; letter-spacing:0.03em; }}
  td {{ padding:12px; border-bottom:1px solid #f0f0f0; }}
  a {{ color:#0b5fff; text-decoration:none; }}
  a:hover {{ text-decoration:underline; }}
  .note {{ margin-top:20px; font-size:12px; color:#999; }}
</style>
</head>
<body>
  <div class="wrap">
    <h1>Daily Sports Card Flip Report</h1>
    <div class="sub">{today} · Using SAMPLE data — not live eBay results yet</div>
    <table>
      <thead>
        <tr><th>Card</th><th>Buy price (+ship)</th><th>Est. resale</th><th>Net profit</th><th>Margin</th></tr>
      </thead>
      <tbody>
        {rows_html}
      </tbody>
    </table>
    <div class="note">Net profit already accounts for eBay final value fees and estimated resale shipping. Comp values are a placeholder data set — connect a real pricing source before acting on this.</div>
  </div>
</body>
</html>"""
