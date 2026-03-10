# 🤖 Folarin's Personalized RAG Chatbot Web App

This is a full-stack Retrieval-Augmented Generation (RAG) chatbot built with:

- 🧠 **Amazon Bedrock** for LLM-powered responses
- 📂 **Amazon S3** as the knowledge base storage
- 🚀 **Node.js + Express** as the backend
- 💬 **Express Handlebars** for frontend rendering
- 🖼️ A styled, responsive chat widget powered by vanilla JS + Tailwind-like styles

> Built and maintained by [Folarin Favour Olaoluwapo](https://www.linkedin.com/in/folarin-favour-olaoluwapo).

## 📌 Project Highlights

- Chatbot answers questions about me, my skills, and projects — all from a custom document
- Toggle between general LLM mode and knowledge base retrieval
- Floating chat UI with modal animations and typing indicators
- API-powered endpoints connected to Amazon Bedrock
- Personalized AI assistant to enhance my portfolio

## 🗂 Project Structure

```
rag-chatbot-webapp/
├── app.js                 # Express server and routes
├── .env                  # AWS credentials and model info
├── /views                # Handlebars templates
│   ├── layouts/
│   │   └── main.hbs
│   └── index.hbs
├── /public               # Static files
│   ├── /css/styles.css
│   ├── /js/app.js
│   └── /images/myImg.jpg
└── package.json
```

## ⚙️ Setup Instructions
there are two js- one is to test the api , api.js while the other is for the server side- app.js

### 1. Clone the Repository
```bash
git clone https://github.com/mr-ffo/rag-chatbot-webapp.git
cd rag-chatbot-webapp
```

### 2. Install Dependencies
```bash
npm install
```

### 3. Create Your `.env` File
```env
AWS_REGION=us-east-2
MODEL_ID=meta.llama3-3-70b-instruct-v1:0
KNOWLEDGE_BASE_ID=your-kb-id
MODEL_ARN=arn:aws:bedrock:us-east-2::foundation-model/meta.llama3-3-70b-instruct-v1:0
```

## 🧠 Bedrock API Endpoints

- `GET /bedrock/query?text=your question` → answers from knowledge base
- `GET /bedrock/invoke?text=your question` → pure LLM response (LLaMA 3)

## 🖼️ UI Features

- Floating action button opens a modern chat modal
- Messages auto-scroll and show typing animation
- Toggle switch to switch between AI modes
- Responsive design using simple utility CSS

## 🔍 Example Queries

- `Who is Folarin Favour?` ✅
- `What projects has he done?` ✅
- `What skills does he have?` ✅

## 🧪 Run the App

```bash
node app.js
```
Visit: [http://localhost:8080](http://localhost:8080)

## 🛠 Tech Stack

| Layer     | Tech                         |
|-----------|------------------------------|
| Frontend  | HTML, Handlebars, JS, CSS    |
| Backend   | Node.js, Express             |
| AI Engine | Amazon Bedrock (LLaMA 3)     |
| Vector DB | Amazon OpenSearch Serverless |
| Storage   | Amazon S3                    |

## 📬 Contact

- [Medium Projects](https://medium.com/@folarin-favour-olaoluwapo)
- [LinkedIn](https://www.linkedin.com/in/folarin-favour-olaoluwapo)
- [GitHub](https://github.com/mr-ffo)

## 💡 License

MIT License. Use freely, personalize it, and deploy your own AI-powered chatbot assistant!