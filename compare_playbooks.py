"""
So sánh chi tiết 2 bản playbook và log ra các thay đổi
"""
import difflib
from pathlib import Path

def parse_playbook(content):
    """Parse playbook thành dictionary với bullet_id làm key"""
    bullets = {}
    lines = content.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if line.startswith('[') and '] helpful=' in line:
            # Extract bullet_id
            bullet_id = line.split(']')[0][1:]
            bullets[bullet_id] = line
    
    return bullets

def compare_playbooks(old_file, new_file):
    """So sánh 2 playbook files"""
    
    print("="*80)
    print("SO SÁNH CHI TIẾT 2 BẢN PLAYBOOK")
    print("="*80)
    
    # Đọc files
    with open(old_file, 'r', encoding='utf-8') as f:
        old_content = f.read()
    
    with open(new_file, 'r', encoding='utf-8') as f:
        new_content = f.read()
    
    # 1. So sánh độ dài
    print("\n📊 1. SO SÁNH ĐỘ DÀI")
    print("-" * 80)
    old_lines = old_content.split('\n')
    new_lines = new_content.split('\n')
    
    print(f"Playbook Cũ:")
    print(f"  - Số dòng: {len(old_lines)}")
    print(f"  - Số ký tự: {len(old_content):,}")
    print(f"  - Kích thước: {len(old_content.encode('utf-8')) / 1024:.2f} KB")
    
    print(f"\nPlaybook Mới:")
    print(f"  - Số dòng: {len(new_lines)}")
    print(f"  - Số ký tự: {len(new_content):,}")
    print(f"  - Kích thước: {len(new_content.encode('utf-8')) / 1024:.2f} KB")
    
    print(f"\nThay đổi:")
    print(f"  - Dòng: {len(new_lines) - len(old_lines):+d} ({(len(new_lines) - len(old_lines)) / len(old_lines) * 100:+.1f}%)")
    print(f"  - Ký tự: {len(new_content) - len(old_content):+,d} ({(len(new_content) - len(old_content)) / len(old_content) * 100:+.1f}%)")
    
    # 2. Parse bullets
    old_bullets = parse_playbook(old_content)
    new_bullets = parse_playbook(new_content)
    
    print(f"\n📋 2. SO SÁNH SỐ LƯỢNG BULLETS")
    print("-" * 80)
    print(f"Playbook Cũ: {len(old_bullets)} bullets")
    print(f"Playbook Mới: {len(new_bullets)} bullets")
    print(f"Thay đổi: {len(new_bullets) - len(old_bullets):+d} bullets")
    
    # 3. Tìm bullets mới
    new_bullet_ids = set(new_bullets.keys()) - set(old_bullets.keys())
    removed_bullet_ids = set(old_bullets.keys()) - set(new_bullets.keys())
    common_bullet_ids = set(old_bullets.keys()) & set(new_bullets.keys())
    
    print(f"\n🆕 3. BULLETS MỚI ĐƯỢC THÊM VÀO ({len(new_bullet_ids)} bullets)")
    print("-" * 80)
    if new_bullet_ids:
        for bullet_id in sorted(new_bullet_ids):
            content = new_bullets[bullet_id]
            # Trích xuất phần content (sau ::)
            if '::' in content:
                desc = content.split('::', 1)[1].strip()
                # Truncate nếu quá dài
                if len(desc) > 100:
                    desc = desc[:100] + "..."
                print(f"\n[{bullet_id}]")
                print(f"  Nội dung: {desc}")
            else:
                print(f"\n[{bullet_id}]")
                print(f"  {content}")
    else:
        print("  (Không có bullets mới)")
    
    # 4. Bullets bị xóa
    print(f"\n🗑️  4. BULLETS BỊ XÓA ({len(removed_bullet_ids)} bullets)")
    print("-" * 80)
    if removed_bullet_ids:
        for bullet_id in sorted(removed_bullet_ids):
            print(f"  - [{bullet_id}]")
    else:
        print("  (Không có bullets bị xóa)")
    
    # 5. Bullets bị thay đổi
    modified_bullets = []
    for bullet_id in common_bullet_ids:
        if old_bullets[bullet_id] != new_bullets[bullet_id]:
            modified_bullets.append(bullet_id)
    
    print(f"\n✏️  5. BULLETS BỊ THAY ĐỔI ({len(modified_bullets)} bullets)")
    print("-" * 80)
    if modified_bullets:
        for bullet_id in sorted(modified_bullets):
            print(f"\n[{bullet_id}]")
            print(f"  Cũ: {old_bullets[bullet_id][:100]}...")
            print(f"  Mới: {new_bullets[bullet_id][:100]}...")
    else:
        print("  (Không có bullets bị thay đổi)")
    
    # 6. Tìm vị trí bắt đầu có sự khác biệt
    print(f"\n📍 6. VỊ TRÍ BẮT ĐẦU CÓ SỰ KHÁC BIỆT")
    print("-" * 80)
    
    differ = difflib.Differ()
    diff = list(differ.compare(old_lines, new_lines))
    
    first_diff_line = None
    for i, line in enumerate(diff):
        if line.startswith('+ ') or line.startswith('- ') or line.startswith('? '):
            # Tìm số dòng tương ứng trong file gốc
            line_num = sum(1 for x in diff[:i] if not x.startswith('+ '))
            first_diff_line = line_num
            break
    
    if first_diff_line is not None:
        print(f"Dòng đầu tiên có sự khác biệt: {first_diff_line}")
        print(f"\nNội dung xung quanh vị trí đó:")
        start = max(0, first_diff_line - 2)
        end = min(len(old_lines), first_diff_line + 3)
        
        print("\n  Playbook Cũ:")
        for i in range(start, end):
            marker = ">>>" if i == first_diff_line else "   "
            if i < len(old_lines):
                print(f"  {marker} {i+1:3d}: {old_lines[i][:80]}")
        
        print("\n  Playbook Mới:")
        new_line_idx = 0
        for i, line in enumerate(diff):
            if not line.startswith('- '):
                if new_line_idx >= start and new_line_idx < end:
                    marker = ">>>" if new_line_idx == first_diff_line else "   "
                    display_line = line[2:] if line.startswith('+ ') or line.startswith('  ') else line
                    print(f"  {marker} {new_line_idx+1:3d}: {display_line[:80]}")
                if not line.startswith('+ '):
                    new_line_idx += 1
    else:
        print("Không tìm thấy sự khác biệt (2 file giống hệt nhau)")
    
    # 7. Chi tiết từng thay đổi
    print(f"\n📝 7. CHI TIẾT CÁC THAY ĐỔI THEO DÒNG")
    print("-" * 80)
    
    changes_count = {'added': 0, 'removed': 0, 'modified': 0}
    
    for line in diff:
        if line.startswith('+ '):
            changes_count['added'] += 1
        elif line.startswith('- '):
            changes_count['removed'] += 1
    
    print(f"Tổng số thay đổi:")
    print(f"  - Dòng thêm vào: {changes_count['added']}")
    print(f"  - Dòng xóa đi: {changes_count['removed']}")
    print(f"  - Tổng cộng: {changes_count['added'] + changes_count['removed']} dòng thay đổi")
    
    # 8. Tóm tắt
    print(f"\n" + "="*80)
    print("📊 TÓM TẮT")
    print("="*80)
    print(f"✅ Bullets mới: {len(new_bullet_ids)}")
    print(f"❌ Bullets xóa: {len(removed_bullet_ids)}")
    print(f"✏️  Bullets sửa: {len(modified_bullets)}")
    print(f"📈 Tăng trưởng: {len(new_bullets) - len(old_bullets):+d} bullets ({(len(new_bullets) - len(old_bullets)) / len(old_bullets) * 100:+.1f}%)")
    print(f"📏 Tăng kích thước: {len(new_content) - len(old_content):+,d} ký tự ({(len(new_content) - len(old_content)) / len(old_content) * 100:+.1f}%)")
    
    if new_bullet_ids:
        print(f"\n🎯 Bullets mới quan trọng:")
        for bullet_id in sorted(new_bullet_ids)[:5]:  # Top 5
            print(f"  - [{bullet_id}]")

if __name__ == "__main__":
    # So sánh playbook từ demo ban đầu vs playbook sau verification
    old_file = "logs/live_demo_manual/final_playbook.txt"
    new_file = "logs/verify_learning_playbook.txt"
    
    # Kiểm tra file tồn tại
    if not Path(old_file).exists():
        print(f"❌ File không tồn tại: {old_file}")
        exit(1)
    
    if not Path(new_file).exists():
        print(f"❌ File không tồn tại: {new_file}")
        exit(1)
    
    print(f"📂 So sánh 2 file:")
    print(f"   Cũ: {old_file}")
    print(f"   Mới: {new_file}\n")
    
    compare_playbooks(old_file, new_file)
