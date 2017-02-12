<link type="text/css" href="component.css" rel="stylesheet">
<h1>LDAP USER ACCOUNTS WITHOUT A CROWD ACCOUNT</h1>
<table>
%for row in rows:
    <tr>
        <td>{{row}} </td>
		<td><a href="/adduser/{{row}}"><button type="button">Add user to Crowd</button></a>
    </tr>
%end
</table>
