import os
import uuid

from LMS.common import Session


class PostService:

    #게시물 파일 등록
    @staticmethod
    def save_post(member_id, title, content, files=None, upload_folder='uploads/'):
        """게시글과 첨부파일을 동시에 저장(트랜잭션 처리)"""

        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                #1. 게시글(posts) 먼저 저장
                sql_post = "INSERT INTO posts(member_id, title, content) VALUES (%s, %s, %s)"
                cursor.execute(sql_post, (member_id, title, content))

                #lastrowid : 방금 INSERT된 게시글의 ID(PK) 가져오기
                post_id = cursor.lastrowid
                #첨부파일 테이블에 들어갈 내용

                #2. 단일 파일 처리

                #3. 다중 파일 처리
                if files:
                    for file in files:
                        if file and file.filename != '':
                            origin_name = file.filename
                            ext = origin_name.rsplit('.', 1)[1].lower()
                            save_name = f"{uuid.uuid4().hex}.{ext}"  #상단에 import uuid
                            file_path = os.path.join(upload_folder, save_name)

                            file.save(file_path)  #서버에 저장(uploads/)

                            #attachments 테이블에 각각 저장
                            sql_file = "INSERT INTO attachments(post_id, origin_name, save_name, file_path) VALUES (%s, %s, %s, %s)"

                            cursor.execute(sql_file, (post_id, origin_name, save_name, file_path))
                conn.commit()
                return True

        except Exception as e:
            print(f"Error saving post : {e}")
            conn.rollback()
            return False

        finally:
            conn.close()
            #save_post(member_id, title, content, files, upload_folder)를 받아 Ture or False로 return

    # 파일게시물 목록
    @staticmethod
    def get_posts():
        """작성자 이름과 첨부파일 개수를 함께 조회"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                # 서브쿼리를 사용하여 해당 게시글에 연결된 첨부파일 개수(file_count)를 가져옵니다.
                sql = """
                        SELECT p.*, m.name as writer_name,
                               (SELECT COUNT(*) FROM attachments WHERE post_id = p.id) as file_count
                        FROM posts p
                        JOIN members m ON p.member_id = m.id
                        ORDER BY p.created_at DESC
                    """
                cursor.execute(sql)
                return cursor.fetchall()
        finally:
            conn.close()

    # 파일게시물 자세히보기
    @staticmethod
    def get_post_detail(post_id):
        """게시글 상세 정보와 첨부파일 정보를 함께 조회"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                # 1. 조회수 증가
                cursor.execute("UPDATE posts SET view_count = view_count + 1 WHERE id = %s", (post_id,))

                # 2. 게시글 정보 조회 (작성자 이름 포함)
                sql_post = """
                        SELECT p.*, m.name as writer_name 
                        FROM posts p
                        JOIN members m ON p.member_id = m.id
                        WHERE p.id = %s
                    """
                cursor.execute(sql_post, (post_id,))
                post = cursor.fetchone()

                # 3. 첨부파일 정보 조회
                cursor.execute("SELECT * FROM attachments WHERE post_id = %s", (post_id,))
                files = cursor.fetchall()

                conn.commit()
                return post, files  #post는 posts에 있는 자료, files는 첨부파일에 대한 자료가 넘어감
        finally:
            conn.close()