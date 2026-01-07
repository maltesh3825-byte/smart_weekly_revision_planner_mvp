import express from "express";
import cors from "cors";

const app = express();

// middleware
app.use(cors());
app.use(express.json());

// test route (VERY IMPORTANT)
app.get("/", (req, res) => {
  res.send("Backend is running 🚀");
});

// example API route
app.post("/api/generate", (req, res) => {
  const { topic } = req.body;

  if (!topic) {
    return res.status(400).json({ error: "Topic is required" });
  }

  res.json({
    questions: [
      `What is ${topic}?`,
      `Explain ${topic}.`,
      `Give applications of ${topic}.`
    ]
  });
});

// 🚨 REQUIRED FOR RAILWAY
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
