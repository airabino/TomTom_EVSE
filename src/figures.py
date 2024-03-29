import os
import sys
import time
import json
import requests
import warnings
import matplotlib
import numpy as np
import numpy.random as rand
import pandas as pd
import geopandas as gpd
import scipy.stats as st
import matplotlib.pyplot as plt
import matplotlib.patches as ptc

import contextily as cx
import xyzservices.providers as xyz

from matplotlib.colors import LinearSegmentedColormap
from mpl_toolkits.axes_grid1 import make_axes_locatable

from scipy.spatial import ConvexHull

from .utilities import IsIterable

#Defining some 5 pronged color schemes
color_scheme_5_0=["#e7b7a5","#da9b83","#b1cdda","#71909e","#325666"]

#Defining some 4 pronged color schemes (source: http://vrl.cs.brown.edu/color)
color_scheme_4_0=["#8de4d3", "#0e503e", "#43e26d", "#2da0a1"]
color_scheme_4_1=["#069668", "#49edc9", "#2d595a", "#8dd2d8"]
color_scheme_4_2=["#f2606b", "#ffdf79", "#c6e2b1", "#509bcf"] #INCOSE IS2023

#Defining some 3 pronged color schemes (source: http://vrl.cs.brown.edu/color)
color_scheme_3_0=["#72e5ef", "#1c5b5a", "#2da0a1"]
color_scheme_3_1=["#256676", "#72b6bc", "#1eefc9"]
color_scheme_3_2=['#40655e', '#a2e0dd', '#31d0a5']
color_scheme_3_3=["#f2606b", "#c6e2b1", "#509bcf"] #INCOSE IS2023 minus yellow

#Defining some 2 pronged color schemes (source: http://vrl.cs.brown.edu/color)
color_scheme_2_0=["#21f0b6", "#2a6866"]
color_scheme_2_1=["#72e5ef", "#3a427d"]
color_scheme_2_2=["#1e4d2b", "#c8c372"] #CSU green/gold

#Named color schemes from https://www.canva.com/learn/100-color-combinations/
colors={
	'day_night':["#e6df44","#f0810f","#063852","#011a27"],
	'beach_house':["#d5c9b1","#e05858","#bfdccf","#5f968e"],
	'autumn':["#db9501","#c05805","#6e6702","#2e2300"],
	'ocean':["#003b46","#07575b","#66a5ad","#c4dfe6"],
	'forest':["#7d4427","#a2c523","#486b00","#2e4600"],
	'aqua':["#004d47","#128277","#52958b","#b9c4c9"],
	'field':["#5a5f37","#fffae1","#524a3a","#919636"],
	'misty':["#04202c","#304040","#5b7065","#c9d1c8"],
	'greens':["#265c00","#68a225","#b3de81","#fdffff"],
	'citroen':["#b38540","#563e20","#7e7b15","#ebdf00"],
	'blues':["#1e1f26","#283655","#4d648d","#d0e1f9"],
	'dusk':["#363237","#2d4262","#73605b","#d09683"],
	'ice':["#1995ad","#a1d6e2","#bcbabe","#f1f1f2"],
}


def BackgroundMap(x,y,margin=.05,zoom='auto'):

	maxx=x.max()
	minx=x.min()
	maxy=y.max()
	miny=y.min()

	west=minx-(maxx-minx)*margin
	east=maxx+(maxx-minx)*margin
	south=miny-(maxy-miny)*margin
	north=maxy+(maxy-miny)*margin

	print(west,south,east,north)

	map_img,map_ext=cx.bounds2img(west,south,east,north,ll=True,
		source=xyz.Esri.WorldStreetMap,zoom=zoom)
	map_img,map_ext=cx.warp_tiles(map_img,map_ext,t_crs='EPSG:4326')

	return map_img,map_ext

def ReturnColorMap(colors):

	if type(colors)==str:
		cmap=matplotlib.cm.get_cmap(colors)
	else:
		cmap=LinearSegmentedColormap.from_list('custom',colors,N=256)

	return cmap

def AddVertexField(graph,field,values):

	for idx,key in enumerate(graph._node.keys()):
		graph._node[key][field]=values[idx]

	return graph

def PlotRoutes(graph,routes,figsize=(8,8),ax=None,cmap=ReturnColorMap('viridis'),
	axes_kwargs={},destination_kwargs={},depot_kwargs={},arrow_kwargs={}):
	
	return_fig=False
	if ax==None:
		fig,ax=plt.subplots(figsize=figsize)
		return_fig=True

	route_depot=np.zeros(len(graph._node))

	for route in routes:
		for destination in route[:-1]:
			route_depot[destination]=route[0]

	graph=AddVertexField(graph,'route_depot',route_depot)

	PlotGraph(graph,ax=ax,field='route_depot',cmap=cmap,
					  scatter_kwargs=destination_kwargs)

	depot_cmap=ReturnColorMap(['none','k'])
	depot_kwargs['ec']=depot_cmap([node['is_depot'] for node in graph._node.values()])

	cmap=ReturnColorMap(['none','whitesmoke'])
	PlotGraph(graph,ax=ax,field='is_depot',cmap=cmap,
					  scatter_kwargs=depot_kwargs)

	PlotRoute(graph,routes,ax=ax,arrow_kwargs=arrow_kwargs)

	ax.set(**axes_kwargs)

	if return_fig:
		return fig


def PlotGraph(graph,figsize=(8,8),ax=None,cmap=ReturnColorMap('viridis'),field=None,
	axes_kwargs={},scatter_kwargs={},line_kwargs={}):
	
	return_fig=False
	if ax==None:
		fig,ax=plt.subplots(figsize=figsize)
		return_fig=True

	coords=np.array([[v['x'],v['y']] for v in graph._node.values()])

	if field is None:
		values=None
	else:
		values=np.array([v[field] for v in graph._node.values()])

	ax.scatter(coords[:,0],coords[:,1],c=values,cmap=cmap,**scatter_kwargs)

	if line_kwargs:
		for v in graph._adj.values():
			for e in v.values():
				ax.plot(e['x'],e['y'],zorder=0,**line_kwargs)

	ax.set(**axes_kwargs)

	if return_fig:
		return fig

def PlotCliques(graph,cliques,r=.05,figsize=(8,8),ax=None,colors='viridis',values=None,
	axes_kwargs={},scatter_kwargs={},line_kwargs={},ploygon_kwargs={},colorbar_kwargs={}):
	
	return_fig=False
	if ax==None:
		fig,ax=plt.subplots(figsize=figsize)
		return_fig=True

	cmap=ReturnColorMap(colors)

	coords=np.array([[v['x'],v['y']] for v in graph._node.values()])

	ax.scatter(coords[:,0],coords[:,1],**scatter_kwargs)

	if line_kwargs:
		for v in graph._adj.values():
			for e in v.values():
				ax.plot(e['x'],e['y'],color='k',zorder=0,**line_kwargs)

	len_cliques=[len(clique) for clique in cliques]
	max_len_clique=max(len_cliques)

	if values is None:
		values=np.ones(len(cliques))/2

	coords=np.array([[v['x'],v['y']] for v in graph._node.values()])
	node_ids=np.array([node_id for node_id in graph._node.keys()])

	for idx,clique in enumerate(cliques):
		
		ploygon_kwargs['fc']=cmap((values[idx]/max(values))*.99999)

		clique_nodes=[node_id in clique for node_id in node_ids]

		PlotQHull(coords[clique_nodes,0],coords[clique_nodes,1],r,
			ax=ax,ploygon_kwargs=ploygon_kwargs)

	ax.set(**axes_kwargs)

	vmin=min(values)
	vmax=max(values)
	sm=plt.cm.ScalarMappable(cmap=cmap,norm=plt.Normalize(vmin=vmin, vmax=vmax))
	plt.colorbar(sm,ax=ax,**colorbar_kwargs)

	if return_fig:
		return fig

def ComputeQHull(x,y,r,q=21):

	n=len(x)

	if not hasattr(r,'__iter__'):
		r=np.ones(n)*r

	theta=np.linspace(0,2*np.pi,q)

	x_out=np.zeros(n*q)
	y_out=np.zeros(n*q)

	#Generating the circular geometries
	for idx in range(n):
		x_out[q*idx:q*(idx+1)]=x[idx]+np.cos(theta)*r[idx]
		y_out[q*idx:q*(idx+1)]=y[idx]+np.sin(theta)*r[idx]

	hull=ConvexHull(np.vstack((x_out,y_out)).T)

	return hull._points[hull.vertices]
	# return np.vstack((x_out,y_out)).T

def PlotQHull(x,y,r,figsize=(8,8),ax=None,q=21,
	axes_kwargs={},ploygon_kwargs={}):
	
	return_fig=False
	if ax==None:
		fig,ax=plt.subplots(figsize=figsize)
		return_fig=True

	coords=ComputeQHull(x,y,r,q)

	ax.fill(coords[:,0],coords[:,1],**ploygon_kwargs)

	ax.set(**axes_kwargs)

	if return_fig:
		return fig

def PlotRoute(graph,routes,figsize=(8,8),ax=None,cmap=ReturnColorMap('viridis'),
	axes_kwargs={},scatter_kwargs={},arrow_kwargs={}):
	
	return_fig=False
	if ax==None:
		fig,ax=plt.subplots(figsize=figsize)
		return_fig=True

	coords=np.array([[v['x'],v['y']] for v in graph._node.values()])

	for route in routes:

		for idx in range(1,len(route)):

			x,y=coords[route[idx-1]]
			dx,dy=coords[route[idx]]-coords[route[idx-1]]

			ax.arrow(x,y,dx,dy,**arrow_kwargs)

	ax.set(**axes_kwargs)

	if return_fig:
		return fig


def PlotLine(x,y,figsize=(8,8),ax=None,line_kwargs={},axes_kwargs={}):

	return_fig=False
	if ax==None:
		fig,ax=plt.subplots(figsize=figsize)
		return_fig=True

	ax.plot(x,y,**line_kwargs)

	ax.set(**axes_kwargs)

	if return_fig:
		return fig

def PlotBar(data,x_shift,figsize=(8,8),ax=None,bar_kwargs={},axes_kwargs={}):

	return_fig=False
	if ax==None:
		fig,ax=plt.subplots(figsize=figsize)
		return_fig=True

	x=[idx for idx in range(len(data))]
	ax.bar(x,data,**bar_kwargs)

	ax.set(**axes_kwargs)

	if return_fig:
		return fig

def PlotCircle(coords,r=1,figsize=(8,8),ax=None,patch_kwargs={},axes_kwargs={}):

	return_fig=False
	if ax==None:
		fig,ax=plt.subplots(figsize=figsize)
		return_fig=True

	if not IsIterable(r):
		r=np.ones(len(coords))*r

	for idx,xy in enumerate(coords):

		ax.add_patch(ptc.Circle(xy,r[idx],**patch_kwargs))

	ax.set(**axes_kwargs)

	if return_fig:
		return fig