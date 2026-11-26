---
title: "Morin Mechanics 2.1: tension in a hanging rope"
date: 2022-09-22
category: notes
description: "Solution to Problem 2.1 of Morin's Introduction to Classical Mechanics, first by intuition and then by analysing an infinitesimal element."
legacy_urls:
  - /physics/2022/09/21/morin-1.html
  - /physics/2022/09/22/morin-1.html
---

# Problem 2.1

## Why this Problem is Cool

The physical aspect is simple enough that we can use it as a toy for understanding how to solve the problem by analyzing an infinitesimally small section.

## Problem

A rope with length $ L $ and mass density per unit length $ \rho $ is suspended vertically from one end. Find the tension as a function of height along the rope.

![A rope of length L hanging from a ceiling, with height y measured upward from its free end](/img/posts/morin-2-1-rope.svg)

## Solution

The tension in the rope is the force that opposes/supports the rope's weight. If we consider the very bottom of the rope, we note that it has no tension at all because there is no rope hanging below it, whereas the top of the rope, at $ L $, is supporting the entire weight of rope below it. So we can say that $ T(0) = 0 $ and $ T(L) = g\rho L $. Using this same logic, we can say that any point on the rope is supporting the weight of the rope below it. Therefore:

$$ T(y) = g\rho y $$

Now let's imagine that the physics of this problem was much less intuitive and so we needed to analyze the problem more mathematically. How would we do that?

First, let's draw the free body diagram for an infinitesimally short section of rope, $ dy $, at a position $ y $ somewhere in the middle. We denote the tension at the bottom of this section as $ T(y) $ and as $ T(y + dy) $ at the top. Also, pulling downwards is the weight of the section of rope which is $ g \rho dy $.

![Free-body diagram of a rope element of length dy: tension T(y+dy) acting upward, tension T(y) and weight ρg dy acting downward](/img/posts/morin-2-1-fbd.svg)

Now, we can observe that the rope is static and not moving, so $ \sum F_y = 0 $ holds true here, and we can write:

$$ \begin{align}
T(y + dy) - T(y) - \rho g dy &= 0 \\
\frac {T(y + dy) - T(y)} {dy} &= \rho g \frac {dy} {dy} \\
\frac {dT(y)} {dy} &= \rho g \\
\end{align} $$

Notice how the left hand side was the infinitesimal version of "rise over run", aka the derivative? Now we just have to integrate along the length of the rope:

$$ \begin{align}
T(y) &= \int^y_0 \rho g dy \\
     &= \rho g \int^y_0 dy \\
\end{align} $$

$$ \boxed {T(y) = \rho gy} $$
