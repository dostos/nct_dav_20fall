var width = 960,
    height = 500;

var grid = d3.layout.grid()
  .size([400, 400]);

var color = d3.scale.linear()
  .interpolate(d3.interpolateHcl)
  .domain([0, 9])
  .range(["rgb(33,49,62)", "rgb(239,238,105)"]);

var size = d3.scale.sqrt()
  .domain([0, 9])
  .range([0, 20]);

var sortBy = {
  id: d3.comparator()
    .order(d3.ascending, function(d) { return d.id; }),
  color: d3.comparator()
    .order(d3.ascending, function(d) { return d.color; })
    .order(d3.descending, function(d) { return d.size; })
    .order(d3.ascending, function(d) { return d.id; }),
  size: d3.comparator()
    .order(d3.descending, function(d) { return d.size; })
    .order(d3.ascending, function(d) { return d.color; })
    .order(d3.ascending, function(d) { return d.id; })
};

var data = d3.range(64).map(function(d) { 
  return {
    id: d,
    size: 1 + Math.floor(Math.random() * 9),
    color: Math.floor(Math.random() * 10)
  }; 
});

var svg = d3.select("body").append("svg")
  .attr({
    width: width,
    height: height
  })
.append("g")
  .attr("transform", "translate(280,50)");

d3.selectAll(".sort-btn")
  .on("click", function(d) {
    d3.event.preventDefault();
    data.sort(sortBy[this.dataset.sort]);
    update();
  });

update();

function update() {
  var node = svg.selectAll(".node")
    .data(grid(data), function(d) { return d.id; });
  node.enter().append("circle")
    .attr("class", "node")
    .attr("r", 1e-9)
    .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; })
    .style("fill", function(d) { return color(d.color); });
  node.transition().duration(1000).delay(function(d, i) { return i * 20; })
    .attr("r", function(d) { return size(d.size); })
    .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });
  node.exit().transition()
    .attr("r", 1e-9)
    .remove();
}