# 스택 / 큐 / 덱 (보너스)

Mini Redis에서 직접 구현한 이중 연결 리스트(`mini_redis/dllist.py`)는 양쪽
끝에서 O(1) 삽입/삭제를 지원하므로, 스택/큐/덱을 모두 그 위에서 그대로
구현할 수 있습니다.

## 스택 (Stack) — LIFO

가장 나중에 넣은 원소가 가장 먼저 나오는 구조입니다.

- `push(x)`: 한쪽 끝(예: front)에 삽입
- `pop()`: 같은 쪽 끝에서 꺼냄

```python
class Stack:
    def __init__(self):
        self._list = DoublyLinkedList()

    def push(self, x):
        self._list.insert_front(x)

    def pop(self):
        return self._list.remove_front()

    def peek(self):
        return self._list.head.data if self._list.head else None
```

`insert_front`/`remove_front`가 O(1)이므로 스택 연산도 O(1)입니다.

## 큐 (Queue) — FIFO

먼저 들어온 원소가 먼저 나오는 구조입니다.

- `enqueue(x)`: 뒤(back)에 삽입
- `dequeue()`: 앞(front)에서 꺼냄

```python
class Queue:
    def __init__(self):
        self._list = DoublyLinkedList()

    def enqueue(self, x):
        self._list.insert_back(x)

    def dequeue(self):
        return self._list.remove_front()
```

## 덱 (Deque) — Double-Ended Queue

양쪽 끝 모두에서 삽입/삭제가 가능한 구조로, 스택과 큐를 모두 포괄합니다.

- `push_front` / `push_back`
- `pop_front` / `pop_back`

`DoublyLinkedList`가 이미 `insert_front`, `insert_back`, `remove_front`,
`remove_back`을 O(1)로 제공하므로, 덱은 사실상 `DoublyLinkedList`를 그대로
노출하는 것과 같습니다.

## Mini Redis와의 연결

- 현재 구현에서 LRU 추적 리스트(`Store.lru_list`)는 사실상 **덱**입니다.
  가장 최근 사용된 키를 `head`(front)로, 가장 오래된 키를 `tail`(back)로
  유지하며, `move_to_front`로 임의 위치의 원소를 front로 옮기는 것도
  "덱에서 임의 노드를 제거한 뒤 front로 재삽입"으로 볼 수 있습니다.
- 해시맵 버킷의 체인 또한 덱(이중 연결 리스트)을 재사용한 것입니다.
- 향후 **커맨드 히스토리** 기능을 추가한다면 스택(최근 명령 되돌아보기)이나
  큐(순서대로 replay)로 자연스럽게 확장할 수 있고, **Pub/Sub**을 추가한다면
  구독자별 메시지 버퍼를 큐로 구현해 재사용할 수 있습니다.
