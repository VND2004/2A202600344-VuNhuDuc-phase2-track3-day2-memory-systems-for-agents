# Lab 17 - Multi-Memory Agent (Skeleton LangGraph Style)

## Cấu trúc
- src/memory_backends.py: 4 memory backends/interface.
- src/agent.py: MemoryState, retrieve_memory router, prompt injection, budget trim, save/update logic.
- src/benchmark.py: chạy 10 multi-turn conversations và sinh BENCHMARK.md.
- data/semantic_corpus.json: mock semantic corpus.
- data/profile_store.json: profile store (long-term).
- data/episodes.json: episodic store.
- REFLECTION.md: privacy và limitation.

## Mapping rubric
1. Full memory stack
- Short-term: ShortTermMemory (sliding window in-memory).
- Long-term profile: LongTermProfileMemory (JSON KV store).
- Episodic: EpisodicMemory (JSON log list).
- Semantic: SemanticMemory (keyword retrieval fallback).

2. State/router + prompt injection
- MemoryState TypedDict trong src/agent.py.
- retrieve_memory(state) gom profile + episodes + semantic + recent conversation.
- Assembled prompt có section [PROFILE], [EPISODIC], [SEMANTIC], [RECENT_CONVERSATION].
- Có trim budget theo memory_budget.

3. Save/update + conflict handling
- Tự động extract/update profile facts từ user text.
- Nếu có câu correction allergy, fact mới được overwrite.
- Episodic memory được ghi khi user đánh dấu đã hoàn thành task.

4. Benchmark
- Chạy src/benchmark.py để tạo BENCHMARK.md với 10 multi-turn conversations.
- So sánh no-memory vs with-memory cho mỗi scenario.

5. Reflection
- Xem REFLECTION.md.

## Cách chạy
Từ thư mục gốc:

python src/benchmark.py

Sau khi chạy xong, file BENCHMARK.md được tạo/cập nhật tại thư mục gốc.
