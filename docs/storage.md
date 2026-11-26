# 중앙 스토리지 및 사용자 분리

중앙 스토리지가 원본이며 OneDrive는 주기적인 암호화 버전형 백업 대상으로만 사용한다. Yontology는 NAS 설치/계정 생성/백업 실행 도구가 아니다. 아래는 배포 계약과 운영 가이드이며 실제 서버 설정은 별도 관리한다.

```text
/srv/storage/
  users/
    user-a/
      Documents/    # Raw Sources
      Obsidian/     # Wiki, source registry, learning, Agent Memory
      Projects/
      Photos/
    user-b/
      Documents/
      Obsidian/
      Projects/
      Photos/
  shared/
    Documents/
    Obsidian/
    Projects/
    Photos/
```

개인 계정은 각자 자신의 홈/개인 Vault에만 접근한다. 공유 자료는 명시적으로 공유 그룹에 허용한 디렉터리에만 저장한다. Linux 사용자·그룹, POSIX ACL, Samba share 권한을 함께 구성하고 Tailscale 접속 권한과 SSH 키를 사용자별로 분리한다. SMB/SSH 포트를 인터넷에 직접 공개하지 않는다. 서버 관리자는 기술적으로 파일에 접근할 수 있으며 관리자에게도 비공개가 필요하면 별도 클라이언트 측 암호화가 필요하다. 공용 Vault는 개인 Vault와 별개의 명시적 scope다. 업무 기밀은 사내 정책에 따라 개인 NAS 및 외부 AI 모델로 보내지 않을 수 있다.

## 배포

서버에 사용자별 Yontology checkout 및 .env를 설정한다. 예시 경로는 실제 계정/마운트에 맞춰 변경한다.

```dotenv
YONTOLOGY_NOTES_DIR="/srv/storage/users/user-a/Obsidian"
YONTOLOGY_RAW_DIR="/srv/storage/users/user-a/Documents"
```

Mac/Windows에서는 개인 SMB share를 마운트하고 Obsidian에 해당 Vault를 연다. 클라이언트 .env에는 실제 마운트 경로를 지정한다. 마운트가 끊겼다면 읽기/쓰기 모두 중지하고 재연결한다. 네트워크 Vault는 파일 변경 감지, 지연, 모바일 지원을 별도로 확인해야 한다. 동시 위키 편집은 소유자를 정해 충돌을 피한다. 서버에는 Obsidian Desktop이 필요하지 않다. 공식 Markdown/Bases/Canvas skills를 재사용하며 별도 Obsidian Sync/Headless를 필수로 하지 않는다.

Task Memory는 SMB 직접 쓰기를 금지하는 운영 계약이다. 서버 파일시스템에서 잠금 및 revision 검사를 수행하도록 SSH로 호출한다. 파일 권한/SMB 설정에서 Task Memory를 읽기 전용으로 노출하고, 권한을 가진 SSH 계정만 수정하게 구성한다. 현재 스크립트 자체가 SMB 마운트 감지나 분산 권한 설정을 자동 수행하지는 않는다.

```bash
# 서버의 SSH host alias, key, known_hosts를 먼저 구성한 뒤 실행
python3 scripts/remote_memory.py --host storage-personal --checkout /home/user-a/Yontology init
python3 scripts/remote_memory.py --host storage-personal --checkout /home/user-a/Yontology show demo TASK-1
python3 scripts/remote_memory.py --host storage-personal --checkout /home/user-a/Yontology checkpoint demo TASK-1 --input /path/to/task.json --expected 0
```

서버에서 직접 실행하는 경우 기존 agent_memory.py 사용. 다른 사용자는 별도 SSH alias/checkout 및 자신의 .env를 사용한다. SSH timeout/실패 후 재시도 전 반드시 show로 revision을 확인한다. 실제 owner 전환은 Skill 정책이며 파일 잠금이 원격 에이전트 실행 자체를 중지시키지는 않는다. Bases는 표시용 Properties만 읽으며 Task 편집은 checkpoint CLI에서 한다.

## Raw / Source Registry / Wiki

원본은 Documents에 두고, Vault의 Agent Memory/sources에 source record를 둔다. 원본은 수정하지 않고 버전·해시·출처를 기록한다. 경로는 raw root 기준 상대 경로, 지식 링크는 Vault 기준 상대 경로다. 동일 원본을 두 곳에 복사하지 않는다. 공식 Obsidian Bases로 source/task 현황을 표시한다. Notion 연동은 현재 로드맵에서 제외하며 필요할 때 별도 검토한다.

## 백업

Restic + rclone을 서버에서 별도 구성하여 OneDrive에 암호화된 스냅샷을 저장한다. 단순 sync/mirror는 삭제 및 손상도 전파하므로 기본 정책으로 사용하지 않는다. 개인·공유 데이터는 권한과 동의에 맞춰 별도 백업 저장소 및 키로 관리한다. 예시 목표: 문서/노트 매시간, 대용량 자료 매일, 일간 30일/주간 12주/월간 12개월 보존. 실제 용량, 비용, RPO에 맞춰 조정한다. OneDrive 용량, 연결 권한, 키 복구, 정기 무결성 검사 및 실제 복원 테스트가 선행되어야 한다. 백업 실패 시 알림 및 재시도 정책을 운영 환경에서 설정한다. 클라우드 백업 자격증명은 에이전트 계정과 Git에 노출하지 않는다.

서버 오프라인 시 중앙 상태 작업을 중단한다. 디스크 하나는 RAID가 아니며 백업 복원이 가능한지 검증해야 한다. NAS 인프라 배포 및 백업 자동화는 별도 범위다.
