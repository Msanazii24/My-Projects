<?php
$con=mysqli_connect("localhost","root","","biblioteque");
$req="select * from livre";
$res=mysqli_query($con,$req);
$nl=mysqli_num_rows($res);
echo "$nl <br>";
echo "<table border='1'><tr><th> identifient </th><th> livre </th><th> auteur </th><th> editeur </th><th> date </th></tr> ";
while ($tl=mysqli_fetch_array($res)){
	echo "<tr><td>$tl[0]</td>
	<td>$tl[1]</td>
	<td>$tl[2]</td>
	<td>$tl[3]</td>
	<td>$tl[4]</td></tr>";
}
echo "</table>";
mysqli_close($con);
?>