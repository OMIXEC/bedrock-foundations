// app.js
const express = require('express');
const AWS = require('aws-sdk');
const dotenv = require('dotenv');
const cors = require('cors');

// Load environment variables from .env file
dotenv.config();

const app = express();
const port = 8080;

// Enable CORS if needed for frontend use
app.use(cors());

// AWS config
const REGION = process.env.AWS_REGION || 'us-east-2';
const KNOWLEDGE_BASE_ID = process.env.KNOWLEDGE_BASE_ID;
const MODEL_ARN = process.env.MODEL_ARN;

// Initialize Bedrock Agent Runtime client
const bedrock = new AWS.BedrockAgentRuntime({ region: REGION });

app.get('/', (req, res) => {
  res.json({ message: 'Welcome to your RAG chatbot API!' });
});

app.get('/bedrock/query', async (req, res) => {
  const text = req.query.text; // ✅ This extracts ?text=... from the URL

  if (!text) {
    return res.status(400).json({ error: 'Missing ?text= query parameter' });
  }

  const params = {
    input: { text },
    retrieveAndGenerateConfiguration: {
      knowledgeBaseConfiguration: {
        knowledgeBaseId: process.env.KNOWLEDGE_BASE_ID,
        modelArn: process.env.MODEL_ARN,
      },
      type: 'KNOWLEDGE_BASE',
    },
  };

  try {
    const response = await bedrock.retrieveAndGenerate(params).promise();
    const result = response?.output?.text || 'No response';
    res.json({ question: text, answer: result });
  } catch (err) {
    console.error('Bedrock error:', err);
    res.status(500).json({ error: err.message });
  }
});


app.listen(port, () => {
  console.log(`Server is running on http://localhost:${port}`);
});
