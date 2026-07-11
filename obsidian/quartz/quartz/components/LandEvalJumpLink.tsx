import { QuartzComponent, QuartzComponentConstructor } from "./types"
// @ts-ignore
import script from "./scripts/landevaljump.inline"

const LandEvalJumpLink: QuartzComponent = () => null

const css = `
.eval-card-list {
  margin-top: 0.5rem;
}

.eval-code-badge {
  flex-shrink: 0;
}

.eval-code-link {
  display: inline-block;
  font-size: 0.8rem;
  font-weight: 700;
  padding: 0.15rem 0.5rem;
  border-radius: 5px;
  background: var(--lightgray);
  color: var(--secondary);
  white-space: nowrap;
  cursor: pointer;
}

/* Clickable card title */
.rml-item-clickable {
  cursor: pointer;
  transition: background 0.12s ease;
  border-radius: 6px;
  padding: 0.3rem 0.4rem;
  margin: -0.3rem -0.4rem;
}
.rml-item-clickable:hover {
  background: var(--lightgray);
}
.rml-item-chevron {
  margin-left: auto;
  font-size: 1.2rem;
  color: var(--gray);
  font-weight: 300;
  flex-shrink: 0;
  line-height: 1;
}

/* Modal overlay */
#eval-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  z-index: 9999;
  display: none;
  align-items: flex-start;
  justify-content: center;
  padding: 2rem 1rem;
  overflow-y: auto;
}
#eval-modal-overlay.eval-modal-open {
  display: flex;
}
body.eval-modal-body-lock {
  overflow: hidden;
}

#eval-modal {
  background: var(--light);
  border-radius: 12px;
  width: 100%;
  max-width: 700px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.22);
  overflow: hidden;
  margin: auto;
}

.eval-modal-loading {
  padding: 2rem;
  text-align: center;
  color: var(--gray);
}

.eval-modal-header {
  background: var(--lightgray);
  padding: 1.25rem 1.5rem 1rem;
  border-bottom: 1px solid var(--lightgray);
}

.eval-modal-title-row {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  flex-wrap: nowrap;
}

.eval-modal-titles {
  flex: 1 1 auto;
  min-width: 0;
}

.eval-modal-land-name {
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--dark);
  line-height: 1.3;
}

.eval-modal-rule-name {
  font-size: 0.88rem;
  color: var(--gray);
  margin-top: 0.2rem;
}

.eval-modal-close {
  flex-shrink: 0;
  background: none;
  border: none;
  font-size: 1.5rem;
  line-height: 1;
  color: var(--gray);
  cursor: pointer;
  padding: 0.1rem 0.3rem;
  border-radius: 4px;
  margin-left: 0.25rem;
}
.eval-modal-close:hover {
  background: var(--lightgray);
  color: var(--dark);
}

.eval-modal-addr {
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: var(--gray);
}

.eval-modal-body {
  padding: 1.25rem 1.5rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.eval-modal-section {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.eval-modal-section-label {
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  display: inline-block;
  width: fit-content;
}
.eval-section-pass {
  background: #dcfce7;
  color: #15803d;
}
.eval-section-fail {
  background: #fee2e2;
  color: #b91c1c;
}
.eval-section-pending {
  background: #fef3c7;
  color: #92400e;
}
.eval-section-finance {
  background: #e0f2fe;
  color: #0369a1;
}

.eval-modal-list {
  margin: 0;
  padding-left: 1.2rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.93rem;
  color: var(--dark);
  line-height: 1.5;
}

.eval-modal-finance-section {
  border-top: 1px solid var(--lightgray);
  padding-top: 0.75rem;
  margin-top: 0.25rem;
}

.eval-modal-finance-note {
  font-size: 0.9rem;
  color: var(--gray);
  margin: 0;
}

.eval-modal-finance-score {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--secondary);
  margin: 0.25rem 0 0;
}

.eval-modal-disclaimer {
  font-size: 0.8rem;
  color: var(--gray);
  margin: 0;
  padding-top: 0.5rem;
  border-top: 1px solid var(--lightgray);
  line-height: 1.5;
}

/* Fail / no-data badge colours */
.eval-badge-fail {
  background: #fee2e2;
  color: #b91c1c;
}
.eval-badge-nodata {
  background: var(--lightgray);
  color: var(--gray);
}

/* Section label colours for new sections */
.eval-section-site {
  background: #ede9fe;
  color: #5b21b6;
}
.eval-section-pollut {
  background: #fce7f3;
  color: #9d174d;
}

/* Info table inside modal */
.eval-modal-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}
.eval-modal-table th {
  text-align: left;
  white-space: nowrap;
  color: var(--gray);
  font-weight: 500;
  padding: 0.3rem 0.75rem 0.3rem 0;
  vertical-align: top;
  width: 7rem;
}
.eval-modal-table td {
  color: var(--dark);
  padding: 0.3rem 0;
  vertical-align: top;
  line-height: 1.5;
}
.eval-modal-table tr + tr th,
.eval-modal-table tr + tr td {
  border-top: 1px solid var(--lightgray);
}

/* Inline tags */
.eval-tag {
  display: inline-block;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.1rem 0.45rem;
  border-radius: 4px;
  margin-right: 0.35rem;
}
.eval-tag-accel {
  background: #d1fae5;
  color: #065f46;
}
.eval-tag-warn {
  background: #fef3c7;
  color: #92400e;
}
`

LandEvalJumpLink.css = css
LandEvalJumpLink.afterDOMLoaded = script

export default (() => LandEvalJumpLink) satisfies QuartzComponentConstructor
