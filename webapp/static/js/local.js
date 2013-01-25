/* Toggles the comment and gene entry areas to appear and disappear based upon whether or not the 
 */ 

function show_hide_comment(id) {
	checkbox = document.getElementById(id + '_cb')
	block = document.getElementById(id + '_block')
	comment_text = document.getElementById(id + '_comment')
	gene_text = document.getElementById(id + '_genes')
	if (!checkbox.checked) {
		block.style.display = 'none';
		comment_text.value = "";
		gene_text.value = "";
	}
	else {
		block.style.display = 'block';
	}
}

function discard_paper(pmid) {

	var url = "/reference/delete/" + pmid;
	$.post(url, function(data) {
		input = "Error:"
		if(data.substring(0, input.length) === input) {
			document.getElementById(pmid + "_validation_error").innerHTML = data
			document.getElementById(pmid + "_validation_error").style.display = 'block';
		}
		else {
			$("#" + pmid).empty().append("<div class='alert alert-success'><h4>Success!</h4>" + data + "</div>");
		}
	});

}

function link_paper(pmid) {
	var url = "/reference/link/" + pmid;
	$.post(url, $("#"+pmid + "_form").serialize(), function(data) {
		input = "Error:"
		if(data.substring(0, input.length) === input) {
			document.getElementById(pmid + "_validation_error").innerHTML = data
			document.getElementById(pmid + "_validation_error").style.display = 'block';		
		}
		else {
			$("#" + pmid).empty().append("<div class='alert alert-success'><h4>Success!</h4>" + data + "</div>");
		}
	});
}

function show_hide_pmid(id) {
	checkbox = document.getElementById(id + '_cb')
	form = document.getElementById(id + '_whole_form')
	whole = document.getElementById(id)
	
	if (checkbox.checked) {
		form.style.display = 'none';
		whole.style.color = '#999';
	}
	else {
		form.style.display = 'block';
		whole.style.color = 'black';
	}
}

function discard_checked_pmids() {
	
	var checkboxes = document.getElementsByName('whole_ref_cb');
	var checkboxesChecked = [];
  	// loop over them all
  	for (var i=0; i<checkboxes.length; i++) {
     	// And stick the checked ones onto an array...
     	if (checkboxes[i].checked) {
        	checkboxesChecked.push(checkboxes[i]);
     	}
  	}

  	if (checkboxesChecked.length>0) {
  		returnStr = '';
  		//concatenate pubmed_ids
  		for (var i=0; i<checkboxesChecked.length; i++) {
  			discard_paper(checkboxesChecked[i].value)
  		}
  	}
	else {
  		document.getElementById("validation_error").innerHTML = "You haven't selected any references.";
  		document.getElementById("validation_error").style.display = 'block';
  }
}

function extract_genes(pmid) {  	
	$.ajax( {
		url: "/reference/extract_genes/" + pmid,
		success: function( data ) {
			$( "#" + pmid + "_genes_area").html(data);
			
			if(data != 'No genes found.') {
				names = data.split(', ');
				highlightStartTag = "<font style='color:blue;'>";
    			highlightEndTag = "</font>";
				for (var i = 0; i < names.length; i++) {
					highlightSearchTerms(names[i], document.getElementById(pmid + "_abstract"), false, false, highlightStartTag, highlightEndTag);
				}
			}
		}
	});
}


function validate(pmid) {
	errors = "";
	
	//Certain tasks must have genes.
	var mustHaveGenes = ["go", "phenotype", "headline", "primary"];
	var mustHaveGenesFull = ["GO information", "Classical phenotype information", "Headline information", "Other Primary Information"];
	for (var i = 0; i < mustHaveGenes.length; i++) {
		var key = "_" + mustHaveGenes[i];
		if (document.getElementById(pmid + key + '_cb').checked && document.getElementById(pmid + key + "_genes").value == "") {
			errors = errors + "Please enter gene names for " + mustHaveGenesFull[i] + ".<br>";
		}
	}
	
	//A gene name can't be used for both Add_to_db and Reviews
	var addToDBGeneNames = document.getElementById(pmid + "_add_to_db_genes").value.replace(new RegExp(",", "gm"), " ").replace(/\|/g, " ").replace(new RegExp(";", "gm"), " ").replace(new RegExp(":", "gm"), " ").split(" ");
	var reviewGeneNames = document.getElementById(pmid + "_review_genes").value.replace(new RegExp(",", "gm"), " ").replace(/\|/g, " ").replace(new RegExp(";", "gm"), " ").replace(new RegExp(":", "gm"), " ").split(" ");
	
	addToDBGeneNames = addToDBGeneNames.filter(function(n) {
		return n.length != 0;
	})
	reviewGeneNames = reviewGeneNames.filter(function(n) {
		return n.length != 0;
	})
	
	filtered = addToDBGeneNames.filter(function(n) {
        return reviewGeneNames.indexOf(n) != -1;
    });
	
	if (filtered.length > 0) {
		errors = errors + "The following gene name(s) were used for two different literature topics: " + filtered + ".<br>";
	}
	
	//The form must have at least one checkbox checked.
	var checked = $("input[@type=checkbox]:checked"); //find all checked checkboxes + radio buttons  
	var nbChecked = checked.size();
	
	if (nbChecked == 0) {
		errors = errors + "You have to check something before pressing the 'Link...' button.<br>";
	}
	
	//If Review is checked without genes, the gene specific tasks should not be checked.
	if (document.getElementById(pmid + "_review_cb").checked && reviewGeneNames.length == 0) {
		for (var i = 0; i < mustHaveGenes.length; i++) {
			var key = "_" + mustHaveGenes[i];
			if (document.getElementById(pmid + key).checked) {
				errors = errors + "If Review is checked with no genes, you cannot check " + mustHaveGenesFull[i] + ".<br>";
			}
		}
	}

	document.getElementById(pmid + "_validation_error").innerHTML = errors
	if (errors == "") {
		document.getElementById(pmid + "_validation_error").style.display = 'none';
		link_paper(pmid);
	}
	else {
		document.getElementById(pmid + "_validation_error").style.display = 'block';
		return false;
	}
}


/* this is used for creating the collapsible section for abstracts */
function activateCollapsible(id) {
	if (window.addEventListener) {
		window.addEventListener("load", function(){makeCollapsible(document.getElementById(id), 1);}, false);
	}
	else if (window.attachEvent) {
		window.attachEvent("onload", function(){makeCollapsible(document.getElementById(id), 1);});
	}
	else {
		window.onload = function(){makeCollapsible(document.getElementById(id), 1);};
	}
}

/* used to bold the author names in the citation */
function bold_citation(count) {
	for (var i = 1; i <= count; i++) {
		citation = document.getElementById('citation' + i);
		citation.innerHTML = citation.innerHTML.replace(/([^0-9]+\([0-9]{4}\))/g, "<strong>$1</strong>");
	}
	return true;
}


/* following methods are used for highlighting the keywords */


/*
 * This is the function that actually highlights a text string by
 * adding HTML tags before and after all occurrences of the search
 * term. You can pass your own tags if you'd like, or if the
 * highlightStartTag or highlightEndTag parameters are omitted or
 * are empty strings then the default <font> tags will be used.
 */
function doHighlight(bodyText, searchTerm, highlightStartTag, highlightEndTag) {
  // the highlightStartTag and highlightEndTag parameters are optional
  if ((!highlightStartTag) || (!highlightEndTag)) {
    highlightStartTag = "<font style='color:blue; background-color:yellow;'>";
    highlightEndTag = "</font>";
  }
  
  // find all occurences of the search term in the given text,
  // and add some "highlight" tags to them (we're not using a
  // regular expression search, because we want to filter out
  // matches that occur within HTML tags and script blocks, so
  // we have to do a little extra validation)
  var newText = "";
  var i = -1;
  var lcSearchTerm = searchTerm.toLowerCase();
  var lcBodyText = bodyText.toLowerCase();
    
  while (bodyText.length > 0) {
    i = lcBodyText.indexOf(lcSearchTerm, i+1);
    if (i < 0) {
      newText += bodyText;
      bodyText = "";
    } else {
      // skip anything inside an HTML tag
      if (bodyText.lastIndexOf(">", i) >= bodyText.lastIndexOf("<", i)) {
        // skip anything inside a <script> block
        if (lcBodyText.lastIndexOf("/script>", i) >= lcBodyText.lastIndexOf("<script", i)) {
          newText += bodyText.substring(0, i) + highlightStartTag + bodyText.substr(i, searchTerm.length) + highlightEndTag;
          bodyText = bodyText.substr(i + searchTerm.length);
          lcBodyText = bodyText.toLowerCase();
          i = -1;
        }
      }
    }
  }
  
  return newText;
}

function simpleHighlight(bodyText, searchTerm, highlightStartTag, highlightEndTag) {
	  // the highlightStartTag and highlightEndTag parameters are optional
  if ((!highlightStartTag) || (!highlightEndTag)) {
    highlightStartTag = "<font style='color:blue; background-color:yellow;'>";
    highlightEndTag = "</font>";
  }
  
	re = new RegExp(searchTerm, "gi");

	func = function(match) {
        return [highlightStartTag, match, highlightEndTag].join("");
    };

	bodyText = bodyText.replace(re, func);

	return bodyText;
}


/*
 * This is sort of a wrapper function to the doHighlight function.
 * It takes the searchText that you pass, optionally splits it into
 * separate words, and transforms the text on the current web page.
 * Only the "searchText" parameter is required; all other parameters
 * are optional and can be omitted.
 */
function highlightSearchTerms(searchText, highlightableArea, treatAsPhrase, warnOnFailure, highlightStartTag, highlightEndTag) {
  // if the treatAsPhrase parameter is true, then we should search for 
  // the entire phrase that was entered; otherwise, we will split the
  // search string so that each word is searched for and highlighted
  // individually
  if (treatAsPhrase) {
    searchArray = [searchText];
  } else {
    searchArray = searchText.split(" ");
  }
  
  if (highlightableArea == null) {
  	if (!document.body || typeof(document.body.innerHTML) == "undefined") {
    	if (warnOnFailure) {
      		alert("Sorry, for some reason the text of this page is unavailable. Searching will not work.");
   	 	}
    	return false;
  	}
  	highlightableArea=document.body;
  }
  
  var bodyText = highlightableArea.innerHTML;
  for (var i = 0; i < searchArray.length; i++) {
    bodyText = simpleHighlight(bodyText, searchArray[i], highlightStartTag, highlightEndTag);
  }
  
  highlightableArea.innerHTML = bodyText;

  return true;
}


function show_hide (buttonId, buttonNm, contentId) {
	if ($('#' + buttonId).val().match('Show')) {
	    $('#' + buttonId).val('Hide ' + buttonNm);
	    $('#' + contentId).show();
	}
	else {
	    $('#' + buttonId).val('Show ' + buttonNm);
            $('#' + contentId).hide();
	}

}


//Downloaded from http://www.acmeous.com/tutorials/demo/acmeousCollapsibleLists/acmeousCollapsibleLists.js

//CONFIGURATION
// collapsedImage='http://www.yeastgenome.org/images/plus.gif';
// expandedImage='http://www.yeastgenome.org/images/minus.gif';
collapsedImage='../static/img/plus.gif';
expandedImage='../static/img/minus.gif';

defaultState=1;	//1 = show, 0 = hide
/* makeCollapsible - makes a list have collapsible sublists
 * 
 * listElement - the element representing the list to make collapsible
 */
function makeCollapsible(listElement,listState) {
  if(listState!=null) defaultState=listState;

  // removed list item bullets and the sapce they occupy
  listElement.style.listStyle='none';
  listElement.style.marginLeft='0';
  listElement.style.paddingLeft='0';

  // loop over all child elements of the list
  var child=listElement.firstChild;
  while (child!=null){

    // only process li elements (and not text elements)
    if (child.nodeType==1){

      // build a list of child ol and ul elements and show/hide them
      var list=new Array();
      var grandchild=child.firstChild;
      while (grandchild!=null){
        if (grandchild.tagName=='OL' || grandchild.tagName=='UL'){
          if(defaultState==1) grandchild.style.display='block';
		  else grandchild.style.display='none';
          list.push(grandchild);
        }
        grandchild=grandchild.nextSibling;
      }

      // add toggle buttons
	  if(defaultState==1) {
		  var node=document.createElement('img');
		  node.setAttribute('src',expandedImage);
		  node.setAttribute('class','collapsibleOpen');
		  node.style.marginRight="5px";
		  node.style.display = "inline";
		  node.onclick=createToggleFunction(node,list);
		  child.insertBefore(node,child.firstChild);
	  } else {
		  var node=document.createElement('img');
		  node.setAttribute('src',collapsedImage);
		  node.setAttribute('class','collapsibleClosed');
		  node.style.marginRight="5px";
		  node.style.display = "inline";
		  node.onclick=createToggleFunction(node,list);
		  child.insertBefore(node,child.firstChild);
	  }
    }

    child=child.nextSibling;
  }

}

/* createToggleFunction - returns a function that toggles the sublist display
 * 
 * toggleElement  - the element representing the toggle gadget
 * sublistElement - an array of elements representing the sublists that should
 *                  be opened or closed when the toggle gadget is clicked
 */
function createToggleFunction(toggleElement,sublistElements) {

  return function() {

    // toggle status of toggle gadget
    if (toggleElement.getAttribute('class')=='collapsibleClosed'){
      toggleElement.setAttribute('class','collapsibleOpen');
      toggleElement.setAttribute('src',expandedImage);
    }else{
      toggleElement.setAttribute('class','collapsibleClosed');
      toggleElement.setAttribute('src',collapsedImage);
    }

    // toggle display of sublists
    for (var i=0;i<sublistElements.length;i++){
      sublistElements[i].style.display=
          (sublistElements[i].style.display=='block')?'none':'block';
    }

  }

}



