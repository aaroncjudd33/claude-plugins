# Teams HTML Formatting Guide

How to write HTML for Teams chat messages that renders cleanly in both light and dark mode.
This guide applies to all plugins, all message types (session updates, CAB notices, story summaries, etc.).

---

## What Teams Renders Well

| Element | Use for |
|---------|---------|
| `<b>` | Section labels, emphasis |
| `<i>` / `<em>` | Signature line, secondary notes |
| `<ul>` / `<li>` | Almost everything — primary layout tool |
| `<hr/>` | Section dividers |
| `<p>` | Intro and closing paragraphs |
| `<br/>` | Vertical spacing between elements |
| `<a href>` | Links |
| `<table>` (2–3 col) | True tabular data only — see rules below |

---

## What to Avoid

| Element | Problem | Use instead |
|---------|---------|-------------|
| `<pre>` | Solid black background — unreadable in dark mode | Nested `<ul>` |
| `<code>` | Dark inline background — clashes in dark mode | Plain text or `<b>` |
| `<h2>` / `<h3>` | Too heavy, over-prominent | `<b>` on its own line |
| `<th>` | Dark bold header, hard to read | `<td>` for all cells |
| 4+ column tables | Too wide, cramped on screen | Bullet list with bold labels |
| Inline CSS | Ignored by Teams entirely | Don't bother |

---

## Section Label Pattern

Do NOT use `<h3>`. Wrap `<b>` in `<p>` so it gets block-level margins above and below:

```
<p><b>Section Title</b></p>
content here
```

Do NOT use bare `<b>Section</b>` — it is inline and sits flush against the `<hr/>` with no breathing room.

---

## Bullet List (primary layout)

Use `<ul>` with bold labels for most structured content — commands, types, scopes, statuses:

```
<ul>
<li><b>Label</b> — description or value</li>
<li><b>Label</b> — description or value</li>
</ul>
```

---

## Nested List (replaces code trees / `<pre>` blocks)

For hierarchical content like lifecycles, steps, or outlines:

```
<ul>
<li><b>Top-level item</b>
  <ul>
    <li>Sub-item one</li>
    <li>Sub-item two</li>
  </ul>
</li>
</ul>
```

---

## Tables (2–3 columns only)

Only use tables for genuinely tabular data (comparisons, two-column lookups).
Use `<td>` for ALL cells — never `<th>` — to avoid dark bold headers.
Add a border and padding so rows are visually separated:

```
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;">
  <tr>
    <td><b>Column A</b></td>
    <td><b>Column B</b></td>
  </tr>
  <tr>
    <td>value</td>
    <td>value</td>
  </tr>
</table>
```

For 4+ columns or anything with long text values, use bullet pairs instead:

```
<ul>
<li><b>Label:</b> value</li>
</ul>
```

### Table Legend

When a table needs a legend, place it immediately after the closing `</table>` tag — no `<br/>` gap between them. Use `<em>` for each legend item to render it as secondary/lighter text. Put each item on its own line:

```
</table>
<em>term = explanation</em><br/>
<em>term = explanation</em><br/>
<em>* = footnote</em>
<br/><br/>
<p><em>Posted by Claude on behalf of Aaron Judd</em></p>
```

### Table Spacing

- `<br/><br/>` between the title and the table
- No gap between table and legend (legend sits flush under the table)
- `<br/><br/>` between legend and signature

---

## Standard Message Template

```
<p><b>Message Title</b></p>
<hr/>
<p>Intro — context, who this is for, why you're sending it.</p>
<hr/>
<p><b>Section One</b></p>
<ul>
  <li><b>Item</b> — detail</li>
</ul>
<hr/>
<p><b>Section Two</b></p>
<ul>
  <li>Sub-item
    <ul>
      <li>Detail</li>
    </ul>
  </li>
</ul>
<hr/>
<p><em>Posted by Claude on behalf of Aaron Judd</em></p>
```

---

## Quick Rules

0. **ALWAYS end every message with the Claude signature** — no exceptions, no matter how short the message:
   `<p><em>Posted by Claude on behalf of Aaron Judd</em></p>`
1. No `<pre>`, no `<code>` — ever
2. No `<h2>`, `<h3>` — use `<p><b>...</b></p>` instead
3. No bare `<b>Section</b>` for headers — always wrap in `<p>` for block-level spacing
4. No `<th>` — use `<td>` with `<b>` inside for header cells
5. No tables wider than 3 columns — use bullet lists
6. No inline CSS — Teams ignores it
7. Nested `<ul>` for any hierarchical or tree-shaped content
8. `<hr/>` between sections for clean visual breaks
