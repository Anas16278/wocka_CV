const { Document, Packer, Paragraph, TextRun, AlignmentType, BorderStyle, UnderlineType, numbering } = require("docx");
const fs = require("fs");

// Get CV data from command line argument
const cvData = JSON.parse(process.argv[2]);

const {
  name, phone, email, location,
  personal_statement,
  job_title, company, duration,
  bullets,
  skills,
  cover_letter
} = cvData;

// ── Horizontal rule via paragraph border ─────────────────────────────────────
function hrLine() {
  return new Paragraph({
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "000000" } },
    spacing: { after: 100 },
  });
}

function sectionHeading(text) {
  return new Paragraph({
    children: [new TextRun({ text, bold: true, size: 24, font: "Calibri" })],
    spacing: { before: 200, after: 60 },
  });
}

function bulletPoint(text) {
  return new Paragraph({
    children: [new TextRun({ text: `• ${text}`, size: 22, font: "Calibri" })],
    spacing: { after: 60 },
    indent: { left: 360 },
  });
}

function bodyText(text) {
  return new Paragraph({
    children: [new TextRun({ text, size: 22, font: "Calibri" })],
    spacing: { after: 80 },
  });
}

function spacer() {
  return new Paragraph({ children: [new TextRun("")], spacing: { after: 80 } });
}

// ── Build CV document ─────────────────────────────────────────────────────────
const cvDoc = new Document({
  sections: [{
    properties: {},
    children: [
      // Name header
      new Paragraph({
        children: [new TextRun({ text: name, bold: true, size: 36, font: "Calibri" })],
        alignment: AlignmentType.CENTER,
        spacing: { after: 60 },
      }),
      // Contact line
      new Paragraph({
        children: [new TextRun({ text: `${phone} | ${email} | ${location}`, size: 20, font: "Calibri" })],
        alignment: AlignmentType.CENTER,
        spacing: { after: 160 },
      }),

      // Personal Statement
      sectionHeading("Personal Statement"),
      hrLine(),
      bodyText(personal_statement),
      spacer(),

      // Work Experience
      sectionHeading("Work Experience"),
      hrLine(),
      new Paragraph({
        children: [
          new TextRun({ text: `${job_title} – ${company}, London`, bold: true, size: 22, font: "Calibri" }),
          new TextRun({ text: `    |    ${duration}`, size: 22, font: "Calibri", color: "555555" }),
        ],
        spacing: { after: 80 },
      }),
      ...bullets.map(b => bulletPoint(b)),
      spacer(),

      // Education
      sectionHeading("Education"),
      hrLine(),
      new Paragraph({
        children: [new TextRun({ text: "GCSEs – 2024", bold: true, size: 22, font: "Calibri" })],
        spacing: { after: 80 },
      }),
      bulletPoint("Mathematics – Grade 5"),
      bulletPoint("English Language – Grade 5"),
      bulletPoint("English Literature – Grade 5"),
      new Paragraph({
        children: [new TextRun({ text: "T-Level in Digital Production, Design and Development (Sixth Form – Ongoing)", bold: true, size: 22, font: "Calibri" })],
        spacing: { before: 100, after: 80 },
      }),
      spacer(),

      // Skills
      sectionHeading("Skills"),
      hrLine(),
      ...skills.map(s => bulletPoint(s)),
      spacer(),

      // References
      sectionHeading("References"),
      hrLine(),
      bodyText("Available upon request."),
    ],
  }],
});

// ── Build Cover Letter document ───────────────────────────────────────────────
const clDoc = new Document({
  sections: [{
    properties: {},
    children: [
      new Paragraph({
        children: [new TextRun({ text: name, bold: true, size: 28, font: "Calibri" })],
        spacing: { after: 40 },
      }),
      new Paragraph({
        children: [new TextRun({ text: `${phone} | ${email}`, size: 20, font: "Calibri" })],
        spacing: { after: 300 },
      }),
      ...cover_letter.split("\n\n").map(para =>
        new Paragraph({
          children: [new TextRun({ text: para.trim(), size: 22, font: "Calibri" })],
          spacing: { after: 200 },
        })
      ),
      spacer(),
      bodyText("Yours sincerely,"),
      spacer(),
      new Paragraph({
        children: [new TextRun({ text: name, bold: true, size: 22, font: "Calibri" })],
      }),
    ],
  }],
});

Promise.all([
  Packer.toBuffer(cvDoc),
  Packer.toBuffer(clDoc),
]).then(([cvBuf, clBuf]) => {
  fs.writeFileSync("/tmp/tailored_cv.docx", cvBuf);
  fs.writeFileSync("/tmp/cover_letter.docx", clBuf);
  console.log("OK");
});
