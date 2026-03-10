const express = require('express');
const AWS = require('aws-sdk');
const dotenv = require('dotenv');
const path = require('path');
const bodyParser = require('body-parser');
const morgan = require('morgan');
const { engine } = require('express-handlebars');

// Load environment variables
dotenv.config();

const app = express();
const port = 8080;

// Middleware
app.use(morgan('dev'));
app.use(bodyParser.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));

// Setup Handlebars view engine
app.engine('handlebars', engine());
app.set('view engine', 'hbs');
app.set('views', path.join(__dirname, 'views'));

// AWS Environment
const AWS_REGION = process.env.AWS_REGION || 'us-east-2';
const MODEL_ID = process.env.MODEL_ID;
const KNOWLEDGE_BASE_ID = process.env.KNOWLEDGE_BASE_ID;
const MODEL_ARN = process.env.MODEL_ARN;

// AWS Clients
const bedrock = new AWS.BedrockRuntime({ region: AWS_REGION });
const bedrockAgent = new AWS.BedrockAgentRuntime({ region: AWS_REGION });

// Routes
app.get('/', (req, res) => {
  res.render('index', { title: 'My RAG Chatbot Portfolio' });

});

app.get('/bedrock/invoke', async (req, res) => {
  const { text } = req.query;
  if (!text || !MODEL_ID) {
    return res.status(400).json({ error: 'Text or MODEL_ID missing' });
  }

  const prompt = `
<|begin_of_text|><|start_header_id|>user<|end_header_id|>
${text}
<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>
`;

  const payload = {
    prompt,
    max_gen_len: 512,
    temperature: 0.5,
  };

  try {
    const response = await bedrock
      .invokeModel({
        modelId: MODEL_ID,
        contentType: 'application/json',
        accept: 'application/json',
        body: JSON.stringify(payload),
      })
      .promise();

    const body = JSON.parse(response.body.toString());
    res.json({ response: body.generation || 'No response' });
  } catch (err) {
    console.error('Invoke Error:', err);
    res.status(500).json({ error: 'Model invocation failed' });
  }
});

app.get('/bedrock/query', async (req, res) => {
  const { text } = req.query;
  if (!text || !KNOWLEDGE_BASE_ID || !MODEL_ARN) {
    return res.status(400).json({ error: 'Missing required input or config' });
  }

  const params = {
    input: { text },
    retrieveAndGenerateConfiguration: {
      knowledgeBaseConfiguration: {
        knowledgeBaseId: KNOWLEDGE_BASE_ID,
        modelArn: MODEL_ARN,
      },
      type: 'KNOWLEDGE_BASE',
    },
  };

  try {
    const result = await bedrockAgent.retrieveAndGenerate(params).promise();
    res.json({ response: result.output.text });
  } catch (err) {
    console.error('RAG Error:', err);
    res.status(500).json({ error: 'Knowledge base query failed' });
  }
});

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});
