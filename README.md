# Mini Redis

바닥부터 구현한 CLI 기반 Mini Redis입니다. 해시맵, 이중 연결 리스트, 힙, 동적 배열을 직접 구현하여
String 명령어, LRU 기반 메모리 관리, TTL 만료 기능을 제공합니다.

## 실행

```bash
python3 main.py
```

```
Mini Redis - type 'exit' or 'quit' to leave.
mini-redis> SET user:2 Alice
OK
mini-redis> GET user:2
"Alice"
mini-redis> DEL user:2
(integer) 1
mini-redis> exit
```

## 테스트

```bash
python3 -m unittest discover -s tests -v
```

## 프로젝트 구조

```
mini_redis/
  dllist.py        이중 연결 리스트 (해시맵 체이닝 + LRU 추적에 재사용)
  hashmap.py        해시맵 (직접 설계한 djb2 해시, 체이닝, load factor 0.75에서 2배 확장)
  dynamic_array.py  동적 배열 (보너스, 힙의 내부 저장소로 사용)
  heap.py            최소 힙 (동적 배열 기반, TTL 만료 시각 추적)
  store.py           String/TTL/메모리 관리 비즈니스 로직 (자료구조 조합)
  cli.py             명령어 파싱/디스패치/Redis 스타일 출력, REPL 루프
main.py              엔트리 포인트
tests/                단위 테스트 (69 tests)
```

## 자료구조 설계

### 이중 연결 리스트 (`dllist.py`)
`prev`/`next`/`data` 필드를 가진 노드 기반 구조. `insert_front`, `insert_back`,
`remove_front`, `remove_back`, `remove_node`, `move_to_front` 모두 노드 참조를
직접 조작하므로 O(1)입니다. 이 구조는 두 곳에서 재사용됩니다.

1. **해시맵의 버킷 체인** — 각 버킷이 하나의 이중 연결 리스트이고, 충돌한
   `(key, value)` 쌍들이 그 안에 체이닝됩니다.
2. **LRU 추적 리스트** — 가장 최근 사용된 키가 항상 `head`에 위치하도록
   `move_to_front`로 갱신됩니다.

### 해시맵 (`hashmap.py`)
- 해시 함수: djb2 (`h = h*33 + ord(ch)`), 짧은 ASCII 키에 대해 충돌이 적게
  퍼지는 간단하고 검증된 함수를 직접 구현했습니다.
- 충돌 해결: 버킷마다 이중 연결 리스트를 두는 체이닝 방식.
- `size / capacity > 0.75`가 되는 순간 버킷 수를 2배로 늘리고 전체 엔트리를
  재해싱(rehash)합니다.
- `put`, `get`, `pop`, `remove`, `contains`, `keys`, `size` 제공.

### LRU (해시맵 + 이중 연결 리스트 조합)
`Store`는 각 키의 `Entry`에 그 키가 위치한 LRU 리스트 노드에 대한 **직접
참조**(`entry.lru_node`)를 들고 있습니다. 그래서:

- `GET`/`SET` 성공 시 → 해시맵으로 O(1)에 Entry를 찾고, Entry가 들고 있는
  노드 참조로 `move_to_front`를 O(1)에 수행합니다 (리스트 전체를 탐색하지 않음).
- 메모리 초과 시 제거 대상 선정 → `lru_list.tail`이 항상 "가장 오래 사용되지
  않은 키"이므로 O(1)에 찾아 제거합니다.

즉, 해시맵이 "키로 노드 찾기"를, 이중 연결 리스트가 "사용 순서 유지 및 이동"을
각각 O(1)에 담당하기 때문에 전체 LRU 추적이 O(1)로 동작합니다.

### 최소 힙 (`heap.py`)
`(expire_at, key)` 튜플을 원소로 갖는 배열 기반 완전 이진 트리입니다.
`_heapify_up`/`_heapify_down`으로 삽입/삭제 시 힙 성질을 O(log n)에 복구하며,
`peek()`으로 "가장 빨리 만료될 키"를 O(1)에 확인할 수 있습니다. 힙이 아니라면
매번 모든 키의 만료 시각을 스캔해야 하므로(O(n)), 만료 관리에 힙이 적합합니다.

**Lazy deletion**: 같은 키에 `EXPIRE`가 여러 번 호출되면 힙에는 오래된
`(expire_at, key)` 항목이 남을 수 있습니다(스택된 stale entry). 삭제 대신,
힙에서 꺼낼 때마다 `Entry.expire_at`과 힙에 저장된 `expire_at`을 비교해서 다르면
그냥 버리는 방식으로 처리합니다. `Store.purge_expired()`가 매 명령 실행 전에
호출되어 힙 top이 이미 만료된 키들을 능동적으로 제거하고(active expiration),
개별 키 조회 시에도 `Entry.expire_at`을 직접 확인하는 수동 체크(passive
expiration)를 병행합니다.

### 동적 배열 (보너스, `dynamic_array.py`)
`append`/`get`/`set`/`remove`/`pop`을 지원하며 용량이 가득 차면 2배로
확장(`_resize`)합니다. 힙의 내부 저장소로 사용되어, "힙이 완전 이진 트리를
배열로 표현한다"는 관점을 그대로 보여줍니다.

## 메모리 관리 + LRU 제거 흐름

`used_memory`는 `Store`가 매 변경마다 증분(incremental)으로 갱신하는
값입니다 (전체 재계산이 아님):

```
used_memory = Σ( len(utf8(key)) + len(utf8(value)) )
```

`SET key value` 처리 순서:

1. 새 엔트리 크기(`len(key)+len(value)`, UTF-8 바이트 기준)가 `maxmemory`보다
   크면 저장하지 않고 즉시 `OOM` 에러를 반환합니다.
2. 기존 키를 덮어쓰는 경우 이전 크기만큼 `used_memory`에서 빼고, TTL을
   초기화하고, LRU에서 맨 앞으로 이동시킵니다. 새 키라면 LRU 맨 앞에 삽입하고
   해시맵에 추가합니다. 어느 경우든 새 크기만큼 `used_memory`를 더합니다.
3. `maxmemory > 0`이고 `used_memory > maxmemory`이면, `used_memory`가
   `maxmemory` 이하가 될 때까지 LRU 리스트의 `tail`(least recently used)부터
   순서대로 제거합니다. 제거마다 해시맵/LRU 리스트에서 함께 삭제하고
   `used_memory`를 줄이고 `evicted_keys`를 1 증가시킵니다.

`INFO memory`는 `used_memory`, `maxmemory`, `evicted_keys` 세 값을 그대로
노출합니다.

## 명령어 요약

| 분류 | 명령어 |
|---|---|
| String | `SET key value`, `GET key`, `DEL key`, `EXISTS key`, `DBSIZE`, `KEYS` |
| 메모리 | `CONFIG SET maxmemory <bytes>`, `INFO memory` |
| TTL | `EXPIRE key seconds`, `TTL key` |
| CLI | `exit` / `quit` |

값에 공백이 필요하면 큰따옴표로 감쌉니다: `SET name "Alice Smith"`.

## 보너스로 구현한 것

- **동적 배열**: `dynamic_array.py`, 힙의 백엔드 저장소로 실사용.
- **스택/큐/덱 개념 정리**: [`STACK_QUEUE_DEQUE.md`](./STACK_QUEUE_DEQUE.md).

이진 트리/BST, Pub-Sub은 이번 구현 범위에는 포함하지 않았습니다.
