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
  text-decoration: none;
  white-space: nowrap;
}

.eval-code-link:hover {
  background: var(--secondary);
  color: var(--light);
}
`

LandEvalJumpLink.css = css
LandEvalJumpLink.afterDOMLoaded = script

export default (() => LandEvalJumpLink) satisfies QuartzComponentConstructor
