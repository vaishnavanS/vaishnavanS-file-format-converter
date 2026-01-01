# EasyConverter

A premium web-based document format converter built with FastAPI and React.

## Deployment to Vercel

To deploy this project:
1. Initialize a Git repository and push the code to GitHub.
2. Connect your GitHub repository to Vercel.
3. Vercel will use the `vercel.json` file provided to build both the React frontend and the FastAPI backend.

### Important Note on Backend
> [!WARNING]
> This application uses `comtypes` for high-quality Word and PowerPoint conversions on Windows. Since Vercel uses Linux servers, these specific features (DOCX to PDF and PPTX to PDF) may require alternative libraries like `LibreOffice` or specialized SaaS APIs to work in production.

## Features
- Interactive Gravity Bubbles background.
- High-quality PDF rendering (300 DPI).
- Support for PDF, DOCX, PPTX, and Image formats.
- Secure file cleanup after download.
