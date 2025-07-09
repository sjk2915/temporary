let isIdAvailable = false;

//아이디 중복 체크 함수
function checkIdDuplicate(){
    let user_id = $("#new-id-check-btn").val()

    $.ajax({
        type:'GET',
        url:"/checkid",
        
        data:{id:user_id},
        success:function(response){
            if (response.result === 'success') {
                alert(response.msg);
                isIdAvailable = true;
            } else {
                alert(response.msg);
                isIdAvailable = false;
            }
        }

    })
}

//회원가입승인함수
function postMember() {
    let new_name = $("#new-name").val();
    let new_id = $("#new-id").val();
    let new_password = $("#new-password").val();
    let check_password = $("#new-password-check").val();
    let new_github = $("#new-github").val();

    let list_form = [new_name, new_id, new_password, new_password, new_github];
    let allFilled = true;

    
    $(".input-check").removeClass("border-red-500").addClass("border-black");

    $(".input-check").each(function(index) {
        if (!list_form[index]) {
            $(this).removeClass("border-black border-b").addClass("border border-red-500");
            allFilled = false;
        }
    });

    $(".input-check").on("focus input", function () {
        $(this).removeClass("border border-red-500").addClass("border-black border-b");
    });


    if (!allFilled) {
        alert("❌입력되지 않은 칸이 있습니다.");
        return;
    }

    if (!isIdAvailable) {
        alert("✅아이디 중복 체크를 먼저 해주세요!");
        return;
    }

    if (new_password !== check_password) {
        alert("❌비밀번호가 일치하지 않습니다!");
        return;
    }


    $.ajax({
        type: 'POST',
        url: "/signup",
        data: {
            name: new_name,
            id: new_id,
            pw: new_password,
            id_github: new_github
        },
        success: function (response) {
            if (response.result === 'success') {
                alert("회원가입 성공!");
                location.href = "/login";
            } else {
                alert("회원가입 실패");
            }
        }
    });
}

function loginSuccess(){
    let user_id = $("#user-id").val()
    let user_password = $("#user-password").val()

    $.ajax({
        type:'POST',
        url:"/login",
        data:{id:user_id , pw:user_password},
        success:function(response){
            if (response.result === 'success') {
                location.href = "/main";

            } else {
                alert("로그인 실패");        
            }
        }
    });
}
