function fireConfetti() {
    confetti({
        particleCount: 200,
        spread: 100,
        origin: { y: 0.4 }
    });
}


//유저가 도전권을 사용하여 도전한 경우 작동하는 함수
function guessMoney(){
    popupSuccess();
    fireConfetti();
    let money = $("#user-input-money").val()
    $.ajax({
        type:"POST",
        url:"/apply",
        data:{appPrice:money},

        error: function (xhr) {
           // xhr.responseJSON
        },

        success:function(response){
            if(response["result"]=="success"){
                alert("도전 성공")
                popupSuccess();
                updateTicketCount();
            }
            else{
                alert("도전 실패")
            }
        }
    })

}
//도전권 획득 및 차감 업데이트 함수
function updateTicketCount() {
    $.ajax({
        type: 'GET',
        url: '/getTicketCount',
        success: function (response) {
            document.getElementById("ticket-count").innerText = `보유 도전권: ${response.appTicket}개`;
        }
    });
}

//완성전


function addCouponAlert(){
    const ticketBtn = document.getElementById('everyCouponAlert')
    ticketBtn.classList.remove('opacity-0', 'pointer-events-none'); // 보이게
    ticketBtn.classList.add('opacity-100'); 

    setTimeout(() => {
        ticketBtn.classList.remove('opacity-100'); 
        ticketBtn.classList.add('opacity-0', 'pointer-events-none'); 
    }, 2000);
}

function addEveryDayTicket(){
    
    $.ajax({
        type:"POST",
        url:"/api/freeEveryTicket",
        data:{userId:id},

        beforeSend: function (xhr) {
            const token = localStorage.getItem('jwt_token');
            if (token) {
                xhr.setRequestHeader('Authorization', token);
            }
        },
        error: function (xhr) {
           // xhr.responseJSON
        },
        success:function(response){
            if(response["result"]=="success"){
                updateTicketCount();
            }
            else{
                addCouponAlert();
            }
        }
    })
}

function addCommitTicket(){
    
    $.ajax({
        type:"POST",
        url:"/api/freeCommitTicket",
        data:{userId:id},

        beforeSend: function (xhr) {
            const token = localStorage.getItem('jwt_token');
            if (token) {
                xhr.setRequestHeader('Authorization', token);
            }
        },
        error: function (xhr) {
           // xhr.responseJSON
        },
        success:function(response){
            if(response["result"]=="success"){
                updateTicketCount();
            }
            else{
                addCouponAlert();
            }
        }
    })
}

function popupSuccess(){
    const successDiv = document.getElementById('popup-user-record');
    if (successDiv.classList.contains('hidden')) {
        successDiv.classList.remove('hidden');
    } 
    else {
    successDiv.classList.add('hidden');
}}

function popupTicket(){
    const ticketDiv = document.getElementById('popup-ticket');
    if (ticketDiv.classList.contains('hidden')) {
        ticketDiv.classList.remove('hidden');
    } 
    else {
    ticketDiv.classList.add('hidden');
}}

function toggle_record(){
    const recordDiv = document.getElementById('past_record');
    if (recordDiv.classList.contains('hidden')) {
        recordDiv.classList.remove('hidden');
    } 
    else {
    recordDiv.classList.add('hidden');
}}






