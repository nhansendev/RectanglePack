# RectanglePack
![image](https://github.com/nhansendev/RectanglePack/assets/9289200/88ebd97b-eb46-49bd-b48c-8b5bd4eae681)
![image](https://github.com/nhansendev/RectanglePack/assets/9289200/2d10fe3e-9c3a-441f-90a6-2274a57fc647)

This Python project expands on the capabilities of the [rectangle-packer](https://github.com/Penlect/rectangle-packer) package primarily by adding efficient rotation checking (missing from the base package) and the ability to maximize area usage of stock.

### Requirements
- Python 3.6+
- rectangle-packer
- matplotlib

### Usage
#### Optimal Packing
```python
from rectangle_packing import find_optimal_packing, plot_positions

# A list of 2-tuples representing the heights and widths of the rectangles to be packed
# Note: units are arbitrary, so just be consistent
sizes = [(4, 3), (4, 3), (2, 2), (2, 2), (3, 1), (8, 7), (7, 8), (2, 10), (1, 1)]

# The width and height of the rectangle that we are packing other rectangles into
stock_width = 20
stock_height = 10

# Find the optimal layout using all shapes, if possible
packed_sizes, positions = find_optimal_packing(sizes, stock_width, stock_height)

# If a valid layout is found, then plot the result
if packed_sizes is not None:
  plot_positions(packed_sizes, positions, stock_width, stock_height)
```

#### Maximize Area Usage
```python
from rectangle_packing import find_max_usage, plot_positions

# A list of 2-tuples representing the heights and widths of the rectangles to be packed
# Note: units are arbitrary, so just be consistent
sizes = [(4, 3), (4, 3), (2, 2), (2, 2), (3, 1), (8, 7), (7, 8), (2, 10), (1, 1)]

stock_width = 15
stock_height = 10

# Try to use as much of the available area as possible, but don't guarantee
# that all shapes will be used
packed_sizes, positions = find_max_usage(sizes, stock_width, stock_height, None)

# If a valid layout is found, then plot the result
if packed_sizes is not None:
  plot_positions(packed_sizes, positions, stock_width, stock_height)
```
