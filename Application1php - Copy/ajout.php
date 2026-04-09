<?php
$con=mysqli_connect("localhost","root","","biblioteque");
$id=$_POST["id"];
$nl=$_POST["nl"];
$au=$_POST["au"];
$edu=$_POST["edu"];
$dp=$_POST["dp"];
$req="select * from livre where id_liv='$id';";
$req1="insert into livre values ('$id','$nl','$au','$edu','$dp');";
$res=mysqli_query($con,$req);
$nbl=mysqli_num_rows($res);
if ($nbl>0)
	echo "id existe";
else{
$res1=mysqli_query($con,$req1);
	if (mysqli_affected_rows($con)==0)
		echo " probleme d'ajout";
	else {
	echo "ajout avec succes";
	
}
}
mysqli_close($con);

?>