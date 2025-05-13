/jarvis-langgraph/
├── app/
│   ├── agents/
│   │   ├── fake_bind_tools.py
│   │   ├── math_tool.py
│   │   ├── ocr_tool.py
│   │   └── tavily_tool.py
│   ├── graph/
│   │   └── langgraph_flow.py
│   ├── api/
│   │   └── app.py
│   └── utils/
│       └── reflection_prompt.py
├── ocr_files/
│   └── (your OCR images here)
├── frontend/
│   └── (basic HTML+JS client for testing)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md

docker-compose down
docker-compose build
docker-compose up -d

docker-compose logs -f

docker system prune -af