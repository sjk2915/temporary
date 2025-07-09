//유저가 갖고 있는 도전권 갯수를 받아오는 함수
//미완성*********
function informTicket(){
    $.ajax({
        type:'GET',
        url:"/api/howManyTicket",
        data:{},
        success:function(response){
            let money_list = response["user-ticket"];
            for(i=0;i<money_list.length;i++){
                showRecords(money_list[i]["guess_money"])
            }
        }
    })

}
//유저가 도전권을 사용하여 도전한 경우 작동하는 함수
function guessMoney(id){
    let money = $("#user-input-money").val()

    $.ajax({
        type:"POST",
        url:"/api/challenge",
        data:{appPrice:money ,userId:id},
        success:function(response){
            if(response["result"]=="success"){
                alert("도전 성공")
                popupSuccess();
                updateTicketCount();
                //도전권 차감(reload) 및 결과 발표 배너 보여주기
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
        url: '/api/ticket',
        success: function (res) {
            document.getElementById("ticket-count").innerText = `보유 도전권: ${res.ticket}개`;
        }
    });
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





