     $(document).ready( function () {

        var oTable = $('#dataset').DataTable( {
        "bJQueryUI": true,
        "bScrollCollapse": true,
        "bAutoWidth": false,
        "bPaginate":false,
        "dom": 'ft',
        "sScrollX": "100%",
        "sScrollXInner": "100%",


         "fnDrawCallback": function( oSettings )
         {
            $('.dataTables_scrollBody table thead tr').css({ 'height' : '0px' });
        },
        "fnInitComplete": function(oSettings, json)
         {
            $('.dataTables_scrollBody table thead tr').css({ 'height' : '0px' });
        },
        "fnRowCallback": function( nRow, aData, iDisplayIndex, iDisplayIndexFull ) {
        switch(aData[1]){
            case '1':
                $(nRow).css('color', 'red')
                break;
        }
        var tab = $('#dataset').DataTable();
        tab.columns(1).visible( false );
    }

        });

    } );


function myFunction() {
            var tab = $('#dataset').DataTable();
            tab.columns(1).visible( false );
            //tab.columns('.column').visible( false );
            for ( var i=1 ; i<4 ; i++ ) {
                tab.columns(i).visible( false );
            }
            tab.columns(':contains(A2V)').visible( true );
            tab.columns.adjust().draw( false ); // adjust column sizing and redraw
        }
$(function () {
  $('[data-toggle="tooltip"]').tooltip({
    container : 'body'
  });


});

//display tooltip left
$('[data-toggle="tool"]').tooltip({
    'placement': 'left'
});



 $('#dataset tbody td.edit').editable( function( sValue ) {
		/* Get the position of the current data from the node */
		 var oTable = $('#dataset').dataTable()
		var aPos = oTable.fnGetPosition( this );

		/* Get the data array for this row */
		var aData = oTable.fnGetData( aPos[0] );

		/* Update the data array and return the value */
		aData[ aPos[2] ] = sValue;
		return sValue;
		/* On DataTable cell select change */

	}, { "onblur": 'submit' } ); /* Submit the form when bluring a field */



