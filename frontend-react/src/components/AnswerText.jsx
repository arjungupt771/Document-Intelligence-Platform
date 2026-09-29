import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const BR = "\uE000"; // private marker for "<br>"

function normalizeAnswer(text) {
  if (!text) return "";
  return (
    text
      .replace(/\r\n/g, "\n")
      // <br>, <br/>, <br />, <BR> -> marker (only this tag is honoured)
      .replace(/<br\s*\/?>/gi, BR)
      // drop breaks at the very start/end of a table cell
      .replace(/\|[ \t]*\uE000+[ \t]*/g, "| ")
      .replace(/[ \t]*\uE000+[ \t]*(?=\|)/g, " ")
      // glued numbered lists outside tables: "... workflow: 1. **A** 2. **B**"
      .replace(/(\S)[ \t]+(\d{1,2})\.[ \t]+(?=\*\*)/g, (m, pre, n) =>
        `${pre}${n === "1" ? "\n\n" : "\n"}${n}. `
      )
      .replace(/^(\*\*[^*\n]{1,60}\*\*)[ \t]+(?=\S)/, "$1\n\n")
      .trim()
  );
}

// Turns the marker into real <br> elements, in tables and paragraphs alike.
function rehypeBreaks() {
  const walk = (node) => {
    if (!node.children) return;
    const out = [];
    for (const child of node.children) {
      if (child.type === "text" && child.value.includes(BR)) {
        const parts = child.value.split(BR);
        parts.forEach((part, i) => {
          if (part) out.push({ type: "text", value: part });
          if (i < parts.length - 1) {
            out.push({ type: "element", tagName: "br", properties: {}, children: [] });
          }
        });
      } else {
        walk(child);
        out.push(child);
      }
    }
    node.children = out;
  };
  return (tree) => walk(tree);
}

const components = {
  // wrap tables so wide ones scroll instead of squashing columns
  table: ({ node, ...props }) => (
    <div className="table-wrap"><table {...props} /></div>
  ),
};

export default function AnswerText({ text }) {
  return (
    <div className="answer md">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeBreaks]}
        components={components}
      >
        {normalizeAnswer(text)}
      </ReactMarkdown>
    </div>
  );
}