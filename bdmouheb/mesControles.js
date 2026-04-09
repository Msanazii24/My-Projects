function trajet(){
	const ad=document.getElementById("ad").value();
	if (ad.length < 3 || ad.length > 30 || ad==""){
		alert("error de longeur de adresse de depart");return false;
	}
}