<?php
$con=mysqli_connect("localhost","root","","BDreclamation");
$req="select nom,prenom,c.telclt,libelle,daterec FROM client c,categorie ca,reclamation r WHERE c.telclt=r.telclt AND ca.idcat=r.idcat and etat='N' ORDER BY libelle,daterec";
$res=mysqli_query($con,$req);
echo('<table  border="1">
  <tbody>
    <tr>
      <th>Nom et prénom</th>
      <th>Téléphone</th>
      <th>Catégorie</th>
      <th>Date de réclamation</th>
    </tr>');
while($l=mysqli_fetch_array($res))
{
	echo("<tr>
      <td>$l[0] $l[1]</td>
      <td>$l[2]</td>
      <td>$l[3]</td>
      <td>$l[4]</td>
    </tr>");
	
}
echo(' </tbody>
</table>
');
mysqli_close($con);
?>