# pip install flask
# 플라스크란?
# 파이썬으로 만든 DB 연동 콘솔 프로그램을 웹으로 연결하는 프레임 워크임
# 프레임워크 : 미리 만들어 놓은 틀 안에서 작업하는 공간
# app.py는 플라스크로 서버를 동작하기 위한 파일명(기본파일)
# static, templates 폴더 필수(프론트용 파일 모이는 곳)
# static : 정적 파일을 모아 놓음(html, css, js)
# templates : 동적 파일을 모아 놓음(crud 화면, 레이아웃, index 등)
# redirect : 다음으로
import os

from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory

from LMS.common import Session
from LMS.domain import Board, Score
from LMS.service import PostService

#                 플라스크    프론트연결     요청,응답   주소전달   주소생성   상태저장소

app = Flask(__name__)
app.secret_key = 'ddfs7err5sts11tfgdaa3a'
#                  여기는 아무 글자나 숫자 써도 됨.
#세션을 사용하기 위해 보안키 설정(아무문자열이나 입력)


#====================================================== Member ======================================================

#1. 로그인
@app.route('/login',methods=['GET','POST'])  #로그인이라는 경로를 만듬(http://localhost:5000/login/)
    # methods는 웹에 동작을 관여한다.
    # GET : URL 주소로 데이터를 처리(보안상 좋지않음, 대신 빠름)
    # POST : body영역에서 데이터를 처리(보안상 좋음, 대용량일때 많이 사용)
    # 대부분 처음에 화면(HTML렌더)을 요청할 때 GET 방식으로 처리
    # 화면에 있는 내용을 백엔드로 전달할 때 POST 방식으로 처리
def login():
    if request.method == 'GET':  #처음 접속하면 GET방식으로 화면 출력
        return render_template('login.html')
        #GET방식으로 요청하면 login.html 화면이 나옴


    #login.html에서 action="login" method="POST" 처리용 코드
    #login.html에서 넘어온 폼 데이터는 uid / upw
    uid = request.form.get('uid')  #요청한 폼 내용을 가져옴
    upw = request.form.get('upw')  #request form get
    # print("/login에서 넘어온 폼 데이터 출력 테스트")
    # print(uid, upw)
    # print("==================================")

    conn = Session.get_connection()  #교사용 db에 접속용 객체
    try:  #예외발생 시 실행
        with conn.cursor() as cursor:  #db에 cursor 객체 사용
            #1. 회원정보 조회
            sql = "SELECT id, name, uid, role\
            FROM members WHERE uid = %s AND password = %s"
            #                  uid가 동일 & pwd가 동일
            # id, name, uid, role 가져온다
            cursor.execute(sql, (uid, upw))
            user = cursor.fetchone()  #쿼리 결과 한개만 가져와 user 변수에 넣음

            if user:
                #찾은 계정이 있으면 브라우저 세션영역에 보관함.
                session['user_id'] = user['id']  #계정 일련번호(회원번호)
                session['user_name'] = user['name']  #계정이름
                session['user_uid'] = user['uid']   #계정로그인명
                session['user_role'] = user['role']   #계정 권한
                #세션에 저장 완료
                #로그인한 정보는 f12 -> application -> cookie -> session에 저장됨
                #session정보를 삭제하면 로그아웃 처리
                return redirect(url_for('index'))
                #처리 후 이동하는 경로(http://localhost:/index로 이동. -> get 메서드 방식)

            else:
                #찾은 계정이 없으면
                return "<script>alert('아이디나 비번이 틀렸습니다.');history.back();</script>"
                #history.back() = 지금보는 화면 바로 전화면으로 (뒤로가기)
                #alert = 경고창

    finally:
        conn.close()   #db연결종료

# 2. 로그아웃
@app.route('/logout')  #원래는 methods=['GET']를 써야하지만 get방식이 기본동작이기 때문에 생략가능.
def logout():
    session.clear()
    return redirect(url_for('login'))  #http://localhost:5000/login(get방식)

# 3. 회원가입
@app.route('/join', methods=['GET','POST'])  #회원가입용 함수
def join():  #http://localhost:5000/ get메서드(화면출력), post(화면폼처리용)
    if request.method == 'GET':
        return render_template('join.html')  #로그인화면용 프론트 연경

    #POST 메서드인 경우(폼으로 데이터가 넘어올때 처리)
    uid = request.form.get('uid')
    password = request.form.get('password')
    name = request.form.get('name')
    #폼에서 넘어온 값을 변수에 넣음

    conn = Session.get_connection()   #db에 연결
    try:  #예외발생 가능성이 있는 코드
        with conn.cursor() as cursor:
            #아이디 중복 확인
            cursor.execute("SELECT id FROM members WHERE uid = %s", (uid,))
            if cursor.fetchone():
                return "<script>alert('이미 존재하는 아이디 입니다.');history.back();</script>"

            #회원정보 저장(role, active는 기본값이 들어감)
            sql = "INSERT INTO members (uid, password, name) VALUES (%s, %s, %s)"
            cursor.execute(sql, (uid, password, name))
            conn.commit()

            return "<script>alert('회원가입이 완료되었습니다.');location.href='/login';</script>"

    except Exception as e:  #예외 발생시 실행문
        print(f"회원가입 에러:{e}")
        return "가입 중 오류가 발생했습니다.\n join()메서드를 확인하세요. "

    finally:  #항상 실행문
        conn.close()

# 내 정보 수정
@app.route('/member/edit', methods=['GET','POST'])
def member_edit():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    #있으면 db연결 시작
    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            if request.method == 'GET':
                #기존 정보 불러오기
                cursor.execute("SELECT * FROM members WHERE id = %s", (session['user_id'],))
                user_info = cursor.fetchone()
                return render_template('member_edit.html', user=user_info)
                #가장 중요한 포인트 : get요청시 페이지(member_edit.html), 객체 전달용 코드(user=user_info)

            #POST 요청 : 정보 업데이트
            new_name = request.form.get('name')
            new_pw = request.form.get('password')

            if new_pw:  #비밀번호 입력시에만 변경
                sql = "UPDATE members SET name = %s, password = %s WHERE id = %s"
                cursor.execute(sql, (new_name, new_pw, session['user_id']))

            else:  #이름만 변경
                sql = "UPDATE members SET name = %s WHERE id = %s"
                cursor.execute(sql, (new_name, session['user_id']))

            conn.commit()
            session['user_name'] = new_name  #세션 이름 정보도 갱신
            return "<script>alert('정보가 수정되었습니다.');location.href='/mypage';</script>"


    except Exception as e:
        print(f"정보 수정 에러:{e}")
        return "수정 중 오류가 발생했습니다.\n member_edit()메서드를 확인하세요."

    finally:
        conn.close()

# 4. 내 정보 조회
@app.route('/mypage')  #http://localhost:5000/mypage  get메서드 요청시 처리
def mypage():
    if 'user_id' not in session:  #로그인상태인지 확인
        return redirect(url_for('login'))  #로그인 아니면 http://localhost:5000/login으로 보냄

    conn = Session.get_connection()  #db연결
    try:
        with conn.cursor() as cursor:
            #1. 내 상세 정보 조회
            cursor.execute("SELECT * FROM members WHERE id = %s", (session['user_id'],))
            #로그인한 정보를 가지고 db에서 찾아옴
            user_info = cursor.fetchone()

            #2. 내가 쓴 게시글 개수 조회(작성한 boards 테이블 활용)
            cursor.execute("SELECT COUNT(*) as board_count FROM boards WHERE member_id = %s", (session['user_id'],))
            #                                                   boards 테이블에 조건 member_id 값을 가지고 찾아옴
            #                갯수를 세어 fetchone()에 넣음 -> board_count 이름으로 갯수를 가지고 있음
            board_count = cursor.fetchone()['board_count']

            return render_template('mypage.html', user=user_info, board_count=board_count)
            #결과를 리턴한다.                     <-    mypage.html 에게 user 객체와 board_count 객체를 담아 보낸
            #프론트에서 사용하려면 {{ user.??? }}으로 작성. ex. {{ board_count }}
    finally:
        conn.close()

#====================================================== Member ======================================================

#====================================================== Board ======================================================

# 글쓰기
@app.route('/board/write',methods=['GET','POST'])  #http://localhost:5000/board/write 경로 생성
def board_write():
    #1. 사용자가 '글쓰기' 버튼을 눌러서 들어왔을 때 화면보여주기
    if request.method == 'GET':
        #로그인 체크(안했으면 글 못쓰게)
        if 'user_id' not in session:
            return '<script>alert("로그인 후 이용 가능합니다.");location.href="/login";</script>'
        return render_template('board_write.html')

    #2. 사용자가 '등록하기' 버튼을 눌러서 데이터를 보냈을 때(DB저장)
    elif request.method == 'POST':  # <form action="/member/edit" method="POST">
        title = request.form.get('title')
        content = request.form.get('content')
        #세션에 저장된 로그인 유저의 id (member_id)
        member_id = session.get('user_id')

        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = "INSERT INTO boards (member_id, title, content) VALUES (%s, %s, %s)"
                cursor.execute(sql, (member_id, title, content))
                conn.commit()
            return redirect(url_for('board_list'))  #저장 후 목록으로 이동
            #redirect : 값이 없이 출력할 때 를 의미(get으로 호출)

        except Exception as e:
            print(f"글쓰기 에러 : {e}")
            return "저장 중 에러가 발생하였습니다."

        finally:
            conn.close()

#1. 게시판 목록 조회
@app.route('/board')  #http://localhost:5000/board
def board_list():
    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            #작성자 이름을 함께 가져오기 위해 JOIN 사용
            sql = """
                SELECT b.*, m.name as writer_name
                FROM boards b
                JOIN members m ON b.member_id = m.id
                ORDER BY b.id DESC
            """

            cursor.execute(sql)
            rows = cursor.fetchall()
            boards = [Board.from_db(row) for row in rows]
            return render_template('board_list.html', boards=boards)

    finally:
        conn.close()

#2. 게시글 자세히보기
@app.route('/board/view/<int:board_id>')  #http://localhost:5000/board/view/99(게시물번호)
def board_view(board_id):
    conn = Session.get_connection()

    try:
        with conn.cursor() as cursor:
            #JOIN을 통해 작성자 정보(name, uid)를 함께 조회
            sql = "SELECT b.*, m.name as writer_name, m.uid as writer_uid FROM boards b JOIN members m ON b.member_id = m.id WHERE b.id = %s"
            cursor.execute(sql, (board_id,))
            row = cursor.fetchone()

            if not row:
                return "<script>alert('존재하지 않은 게시글 입니다.');history.back();</script>"

            #Board 객체로 변환(앞서 작성한 Board.py의 from_db활용)
            board = Board.from_db(row)
            return render_template('board_view.html', board=board)

    finally:
        conn.close()

#3. 게시글 자세히보기
@app.route('/board/edit/<int:board_id>', methods=['GET', 'POST'])
def board_edit(board_id):
    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            #1.화면 보여주기(기존 데이터 로드)
            if request.method == 'GET':
                sql = "SELECT * FROM boards WHERE id = %s"
                cursor.execute(sql, (board_id,))
                row = cursor.fetchone()

                if not row:
                    return "<script>alert('존재하지 않은 게시글 입니다.');history.back();</script>"

                #본인 확인 로직(필요시 추가)
                if row['member_id'] != session.get('user_id'):
                    return "<script>alert('수정 권한이 없습니다..');history.back();</script>"
                print(row)  #콘솔에 테스트 출력용, 없어두댐
                board = Board.from_db(row)
                return render_template('board_edit.html', board=board)

            #2. 실제 DB 업데이트 처리
            elif request.method == 'POST':
                title = request.form.get('title')
                content = request.form.get('content')

                sql = "UPDATE boards SET title=%s, content=%s WHERE id=%s"
                cursor.execute(sql, (title, content, board_id))
                conn.commit()
                return redirect(url_for('board_view', board_id=board_id))

    finally:
        conn.close()

#3. 게시글 삭제
@app.route('/board/delete/<int:board_id>')
def board_delete(board_id):
    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "DELETE FROM boards WHERE id = %s"  #저장된 테이블면 boards 사용
            cursor.execute(sql, (board_id,))
            conn.commit()

            if cursor.rowcount > 0:
                print(f"{board_id}번 게시글 삭제 성공")
            else:
                return "<script>alert('삭제할 게시글이 없거나 권한이 없습니다.');history.back();</script>"

        return redirect(url_for('board_list'))

    except Exception as e:
        print(f"삭제 에러 : {e}")
        return "삭제 중 오류가 발생했습니다."

    finally:
        conn.close()

#====================================================== Board ======================================================

#====================================================== Score ======================================================
#주의사항 :  role에 admin과 manager만 cud를 제공해야함.
#일반 사용자는 role = user, 자신의 성적만 확인 가능

#성적 입력
@app.route('/score/add')  #http://localhost:4000/score/add?uid=teat1&name=test1
def score_add():
    if session.get('user_role') not in ('admin', 'manager'):
        return "<script>alert('권한이 없습니다.'); history.back();</script>"

    target_uid = request.args.get('uid')
    target_name = request.args.get('name')
    # args.get : 주소(url)를 통해서 넘어오는 값, 주소 뒤에 ?key=value&key=value...으로 작성 가능
    # args.form : 폼을 통해서 넘어오는 값

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            #1. 대상 학생의 id 찾기(insert와 update 합쳐서 indate라고 함(수정,삽입))
            cursor.execute("SELECT id FROM members WHERE uid = %s", (target_uid,))
            student = cursor.fetchone()

            #2. 기존성적이 있는지 조회
            existing_score = None
            if student:
                cursor.execute("SELECT * FROM scores WHERE member_id = %s", (student['id'],))
                row = cursor.fetchone()
                print(row)  #테스트용으로 dict 타입으로 콘솔 출력

                if row:
                    #기존에 있던 Score.from_db활용
                    existing_score = Score.from_db(row)
                    #위쪽에 객체 로드 처리 : from LMS.domain import Score
            return render_template('score_form.html', target_uid = target_uid, target_name = target_name, existing_score=existing_score)
                    #render_template : html에 score 객체 전달

    finally:
        conn.close()

#성적 저장
@app.route('/score/save', methods=['POST'])
def score_save():
    if session.get('user_role') not in ('admin', 'manager'):
        return "권한 오류", 403
        # 웹페이지에 오류 페이지로 교체

    #폼 데이터 수집
    target_uid = request.form.get('target_uid')
    kor = int(request.form.get('korean', 0))
    eng = int(request.form.get('english', 0))
    math = int(request.form.get('math', 0))

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            #1. 대상 학생의 id(pk) 가져오기 -> 학생의 번호를 가져옴
            cursor.execute("SELECT id FROM members WHERE uid = %s", (target_uid,))
            student = cursor.fetchone()
            print(student)  #학번 출력
            if not student:
                return "<script>alert('존재하지 않는 학생입니다.');history.back();</script>"

            #2. Score 객체 생성(계산 프로퍼티 활용)
            temp_score = Score(member_id=student['id'], kor=kor, eng=eng, math=math)
            #            (클래스) __init__ 활용하여 객체 생성

            #3. 기존 데이터가 있는지 확인
            cursor.execute("SELECT id FROM scores WHERE member_id = %s", (student['id'],))
            is_exist = cursor.fetchone()  #성적이 있으면 id가 나오고, 없으면 None 처리

            if is_exist:
                #UPDATE문 실행
                sql = "UPDATE scores SET korean=%s, english=%s, math=%s, total=%s, average=%s, grade=%s WHERE member_id = %s"

                cursor.execute(sql, (temp_score.kor, temp_score.eng, temp_score.math, temp_score.total, temp_score.avg, temp_score.grade, student['id']))

            else:
                #INSERT문 실행
                sql = "INSERT INTO scores (member_id, korean, english, math, total, average, grade) VALUES (%s, %s, %s, %s, %s, %s, %s)"

                cursor.execute(sql, (student['id'], temp_score.kor, temp_score.eng, temp_score.math, temp_score.total, temp_score.avg, temp_score.grade))

            conn.commit()
            return f"<script>alert('{target_uid} 학생 성적 저장 완료!');location.href='/score/list';</script>"

    finally:
        conn.close()

#성적 리스트
@app.route('/score/list')  #http://localhost:5000/score/list -> get방식
def score_list():
    #1. 권한 체크(관리자나 매니저만 볼 수 있게 설정)
    if session.get('user_role') not in ('admin', 'manager'):
        return "<script>alert('권한이 없습니다.');history.back();</script>"

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            #2. JOIN을 사용하여 학생이름(name)과 성적 데이터를 함께 조회
            #성적이 없는 학생은 제외하고, 성적이 있는 학생들만 총점 순으로 정렬
            sql = "SELECT m.name, m.uid, s.* FROM scores s JOIN members m ON s.member_id = m.id ORDER BY s.total DESC"
            cursor.execute(sql)
            datas = cursor.fetchall()
            print(f"sql 테스트 결과 : {datas}")

            #3. DB에서 가져온 딕셔너리 리스트를 Score 객체 리스트로 변환
            score_objects = []
            for data in datas:
                #Score 클래스에 정의한 from_db 활용
                s = Score.from_db(data)  #직렬화(dict타입을 객체로 만들음)
                #객체를 리스트화 시켜야 하기 때문에 사용함(문자열은 주소가 없기 때문에 객체로 만듦)
                #객체에 없는 이름(name) 정보는 수동으로 살짝 넣어주기(JOIN에서 만든 값 사용)
                s.name = data['name']
                s.uid = data['uid']
                score_objects.append(s)  #객체를 리스트에 넣음

            return render_template('score_list.html', scores=score_objects)
            # score_list.html : 프론트화면 ui에 -> score_objects=score_object: 성적이 담긴 리스트 객체 전달

    finally:
        conn.close()

#개별 성적 입력하기
@app.route('/score/members')
def score_members():
    if session.get('user_role') not in ('admin', 'manager'):
        return "<script>alert('권한이 없습니다.');history.back();</script>"

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            #LEFT JOIN을 통해 성적이 있으면 s.id가 숫자로, 없으면 NULL로 나옴.
            sql = "SELECT m.id, m.uid, m.name, s.id AS score_id FROM members m LEFT JOIN scores s ON m.id = s.member_id WHERE m.role='user' ORDER BY m.name ASC"
            cursor.execute(sql)
            members = cursor.fetchall()
            return render_template('score_members_list.html', members=members)

    finally:
        conn.close()

#내점수 확인하기
@app.route('/score/my')  #http://localhost:5000/score/my -> get 방식
def score_my():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            #내 ID로만 조회
            sql = "SELECT * FROM scores WHERE member_id = %s"
            cursor.execute(sql, (session['user_id'],))
            row = cursor.fetchone()
            print(row)  #dict 타입으로 결과물 출력

            #Score 객체로 변환(from_db활용)
            score = Score.from_db(row) if row else None

            return render_template('score_my.html', score=score)

    finally:
        conn.close()

#====================================================== Score ======================================================

#==================================================== File Board ====================================================

#파일 처리용 게시판 특징
#1. 파일 업로드 / 다운로드 가능
#2. 단일파일 / 다중파일 업로드 처리
#3. 서비스 패키지 활용
## 4. /upload 라는 폴더 사용 예정 (용량 제한 : 16MB)
#5. 파일명 중복 방지용 코드 활용
#6. DB에서 부모객체가 삭제되면 자식 객체도 삭제되도록 cascade 처리

UPLOAD_FOLDER = 'uploads/'
#폴더가 없으면 자동 생성
if not os.path.exists(UPLOAD_FOLDER):  #import os 상단 추가
    os.makedirs(UPLOAD_FOLDER)
    #폴더 생성용 코드 : os.makedirs(이름)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
#최대 업로드 용량 제한 (ex. 16MB)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
#            bit -> 0,1을 의미
#            1 byte -> 8bit : 0~255 (256개의 값을 가짐)
#            1KB -> 1024byte :
#            1MB -> 1024kbyte
#            1GB -> 1024Mbyte
#            1TB -> 1024Gbyte
#            1PB -> 1024Tbyte
#            1XB -> 1024Pbyte

#게시글 작성하기(파일첨부)
@app.route('/filesboard/write', methods=['GET','POST'])
def filesboard_write():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        #핵심 : getlist를 사용해야 리스트 형태로 가져옴!
        files = request.files.getlist('files')
        # 파일 처리시 html에 필수 코드 : enctype="multipart/form-data"

        if PostService.save_post(session['user_id'], title, content, files):
            return "<script>alert('게시글이 등록되었습니다.');location.href='/filesboard';</script>"

        else:
            return "<script>alert('게시글 등록에 실패하였습니다.');history.back();</script>"

    return render_template('filesboard_write.html')

#게시판 목록 확인하기
@app.route('/filesboard')
def filesboard_list():
    posts = PostService.get_posts()
    return render_template('filesboard_list.html', posts=posts)

# 파일 게시판 상세 보기
@app.route('/filesboard/view/<int:post_id>')
def filesboard_view(post_id):
    post, files = PostService.get_post_detail(post_id)
    if not post:
        return "<script>alert('해당 게시글이 없습니다.'); location.href='/filesboard';</script>"
    return render_template('filesboard_view.html', post=post, files=files)

# send_from_directory 사용하여 자료 다운로드 가능
@app.route('/download/<path:filename>')
def download_file(filename):
    # 파일이 저장된 폴더(uploads)에서 파일을 찾아 전송합니다.
    # 프론트 <a href="{{ url_for('download_file', filename=file.save_name) }}" ...> 이부분 처리용
    # filename은 서버에 저장된 save_name입니다.
    # 브라우저가 다운로드할 때 보여줄 원본 이름을 쿼리 스트링으로 받거나 DB에서 가져와야 합니다.
    origin_name = request.args.get('origin_name')
    return send_from_directory('uploads/', filename, as_attachment=True, download_name=origin_name)
    # from flask import send_from_directory 필수

    #   return send_from_directory('uploads/', filename)는 브라우져에서 바로 열어버림
    #   as_attachment=True 로 하면 파일 다운로드 창을 띄움
    #   저장할 파일명은 download_name=origin_name 로 지정

@app.route('/filesboard/delete/<int:post_id>')
def filesboard_delete(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # 삭제 전 작성자 확인을 위해 정보 조회
    post, _ = PostService.get_post_detail(post_id)
    # _은 리턴값을 사용하지 않겠다 라는 관례적인 표현 (_) 사용하지 않는 변수

    if not post:
        return "<script>alert('이미 삭제된 게시글입니다.'); location.href='/filesboard';</script>"

    # 본인 확인 (또는 관리자 권한)
    if post['member_id'] != session['user_id'] and session.get('user_role') != 'admin':
        return "<script>alert('삭제 권한이 없습니다.'); history.back();</script>"

    if PostService.delete_post(post_id):
        return "<script>alert('성공적으로 삭제되었습니다.'); location.href='/filesboard';</script>"
    else:
        return "<script>alert('삭제 중 오류가 발생했습니다.'); history.back();</script>"

# 게시글 다중파일 수정용
@app.route('/filesboard/edit/<int:post_id>', methods=['GET', 'POST'])
def filesboard_edit(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        files = request.files.getlist('files')  # 다중 파일 가져오기

        if PostService.update_post(post_id, title, content, files):
            return f"<script>alert('수정되었습니다.'); location.href='/filesboard/view/{post_id}';</script>"
        return "<script>alert('수정 실패'); history.back();</script>"

    # GET 요청 시 기존 데이터 로드
    post, files = PostService.get_post_detail(post_id)
    if post['member_id'] != session['user_id']:
        return "<script>alert('권한이 없습니다.'); history.back();</script>"

    return render_template('filesboard_edit.html', post=post, files=files)



#==================================================== File Board ====================================================






#====================================================== Items ======================================================

@app.route('/')  #url 생성 코드(http://localhost:5000/ or http://192.168.0.???:5000)
def index():
    return render_template('main.html')
    # render_template : 웹브라우저로 보낼 파일명
    # templates 라는 폴더에서 main.html을 찾아 보냄

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    # host='0.0.0.0' 누가 요청하면 응답해라
    # port = 5000  플라스크에서 사용하는 포트번호
    # debug=True  콘솔에서 디버그를 보겠다.

