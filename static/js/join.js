let isIdAvailable = false;

//아이디가 중복된 아이디인지를 확인하는 함수임
function checkIdDuplicate(){
    let user_id = $("#new-id-check-btn").val()

    $.ajax({
        type:'POST',
        url:"/api/checkDuplicate",
        
        data:{id:user_id},
        success:function(response){
            if (response.result === 'success') {
                alert("사용 가능한 아이디입니다!");
                isIdAvailable = true;
            } else {
                alert("이미 사용 중인 아이디입니다.");
                isIdAvailable = false;
            }
        }

    })
}
//회원가입을 위한 함수
//아이디 중복 체크를 통과해야 하며
//비밀번호 체크 여부가 확인되어야 서버에 정보를 전송함
function postMember() {
    let new_name = $("#new-name").val();
    let new_id = $("#new-id").val();
    let new_password = $("#new-password").val();
    let check_password = $("#new-password-check").val();
    let new_github = $("#new-github").val();


    if (!isIdAvailable) {
        alert("아이디 중복 체크를 먼저 해주세요!");
        return;
    }


    if (new_password !== check_password) {
        alert("비밀번호가 일치하지 않습니다!");
        return;
}

    
    $.ajax({
        type: 'POST',
        url: "/api/newMember",
        data: {
            name: new_name,
            id: new_id,
            pw: new_password,
            id_github: new_github
        },
        success: function (response) {
            if (response.result === 'success') {
                alert("회원가입 성공!");
                location.href = "login.html";
            } else {
                alert("회원가입 실패");
            }
        }
    });
}
//로그인 성공한 경우 서버에 유저에 대한 정보넘김 
//특정 사람에 대한 정보를 보여주기 위함
function loginSuccess(){
    let user_id = $("#user-id").val()
    let user_password = $("#user-password").val()

    $.ajax({
        type:'POST',
        url:"/api/loginSuccess",
        
        data:{id:user_id , pw:user_password},
        success:function(response){
            if (response.result === 'success') {
                alert("로그인 성공!");   
            } else {
                alert("로그인 실패");        
            }
        }

    })

}

//기존회원임을 확인하는 함수

function handleLogin(){
    let user_id = $("#user-id").val()
    let user_password = $("#user-password").val()

    $.ajax({
        type:'POST',
        url:"/api/loginTry",
        
        data:{id:user_id},
        success:function(response){
            if (response.result === 'success') {
                alert("로그인 성공!");
                loginSuccess();       
                location.href = "main.html";      
            } else {
                alert("로그인 실패");        
            }
        }

    })
}

