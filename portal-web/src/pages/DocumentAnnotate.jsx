import React, { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Document, Page, pdfjs } from 'react-pdf';
import { Canvas, Rect, Circle, IText, Line, Triangle, Group, PencilBrush } from 'fabric';
import api from '../services/api';
import { useNotification } from '../components/Notification';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// Set up PDF.js worker - use the version bundled with react-pdf
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

const DocumentAnnotate = () => {
  const { documentId } = useParams();
  const navigate = useNavigate();
  const { showNotification } = useNotification();

  const [documentData, setDocumentData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [fileUrl, setFileUrl] = useState(null);
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [scale, setScale] = useState(1.2);
  const [isSaving, setIsSaving] = useState(false);

  // Canvas refs
  const canvasRef = useRef(null);
  const fabricCanvasRef = useRef(null);
  const containerRef = useRef(null);

  // Drawing tools state
  const [activeTool, setActiveTool] = useState('select');
  const [brushColor, setBrushColor] = useState('#FF0000');
  const [brushWidth, setBrushWidth] = useState(3);
  const [textInput, setTextInput] = useState('');

  const loadDocument = useCallback(async () => {
    try {
      // Get document metadata
      const response = await api.get(`/api/documents/${documentId}`);
      setDocumentData(response.data);

      // Get presigned URL for the file
      const downloadResponse = await api.get(`/api/documents/${documentId}/download`);
      setFileUrl(downloadResponse.data.url);
    } catch (_error) {
      showNotification('Σφάλμα φόρτωσης εγγράφου', 'error');
      navigate('/documents');
    } finally {
      setLoading(false);
    }
  }, [documentId, navigate, showNotification]);

  const loadAnnotations = useCallback(async () => {
    if (!fabricCanvasRef.current) {
      console.log('Canvas not ready');
      return;
    }

    try {
      console.log('Fetching annotations for document:', documentId);
      const response = await api.get(`/api/annotations/document/${documentId}`);
      const annotations = response.data;
      console.log('Received annotations:', annotations.length);

      // Filter annotations for current page
      const pageAnnotations = annotations.filter((a) => a.page_number === pageNumber);
      console.log('Page annotations:', pageAnnotations.length);

      if (pageAnnotations.length > 0) {
        // Load the most recent annotation
        const latestAnnotation = pageAnnotations.sort(
          (a, b) => new Date(b.created_at) - new Date(a.created_at)
        )[0];

        if (latestAnnotation.content) {
          const content = JSON.parse(latestAnnotation.content);
          console.log('Loading content with objects:', content.objects?.length || 0);
          
          // Clear canvas before loading
          fabricCanvasRef.current.clear();
          
          // Fabric.js v6 loadFromJSON returns a promise
          await fabricCanvasRef.current.loadFromJSON(content);
          
          // Force canvas to render by manipulating the underlying HTML canvas
          const canvas = fabricCanvasRef.current;
          const lowerCanvas = canvas.getElement();
          const upperCanvas = canvas.upperCanvasEl;
          
          // Ensure canvas elements are visible and properly sized
          if (lowerCanvas) {
            lowerCanvas.style.display = 'block';
          }
          if (upperCanvas) {
            upperCanvas.style.display = 'block';
          }
          
          // Multiple render calls to ensure visibility
          canvas.calcOffset();
          canvas.renderAll();
          
          // Force a reflow/repaint by toggling visibility
          if (lowerCanvas) {
            const currentDisplay = lowerCanvas.style.display;
            lowerCanvas.style.display = 'none';
            // eslint-disable-next-line no-unused-expressions
            lowerCanvas.offsetHeight; // Force reflow
            lowerCanvas.style.display = currentDisplay;
          }
          
          canvas.requestRenderAll();
          console.log('Annotations loaded and rendered');
        }
      }
    } catch (_error) {
      console.log('Error loading annotations:', error);
    }
  }, [documentId, pageNumber]);

  // Track if initial load has happened
  const initialLoadDone = useRef(false);
  const canvasInitialized = useRef(false);

  useEffect(() => {
    loadDocument();
  }, [loadDocument]);

  // Initialize Fabric.js canvas
  const initCanvas = useCallback(() => {
    if (canvasRef.current && !canvasInitialized.current) {
      canvasInitialized.current = true;
      
      // Get container dimensions before creating canvas
      const rect = containerRef.current?.getBoundingClientRect() || { width: 800, height: 600 };
      
      // Set HTML canvas dimensions directly first
      canvasRef.current.width = rect.width;
      canvasRef.current.height = rect.height;
      
      fabricCanvasRef.current = new Canvas(canvasRef.current, {
        isDrawingMode: false,
        selection: true,
        width: rect.width,
        height: rect.height,
        renderOnAddRemove: true,
      });

      // Set canvas size based on container
      const updateCanvasSize = () => {
        if (containerRef.current && fabricCanvasRef.current) {
          const rect = containerRef.current.getBoundingClientRect();
          // Update HTML canvas element dimensions
          canvasRef.current.width = rect.width;
          canvasRef.current.height = rect.height;
          // Fabric.js v6 uses setDimensions instead of setWidth/setHeight
          fabricCanvasRef.current.setDimensions({
            width: rect.width,
            height: rect.height
          });
          fabricCanvasRef.current.calcOffset();
          fabricCanvasRef.current.renderAll();
        }
      };

      updateCanvasSize();
      window.addEventListener('resize', updateCanvasSize);

      return () => {
        window.removeEventListener('resize', updateCanvasSize);
      };
    }
  }, []);

  // Load canvas and annotations when document is ready
  useEffect(() => {
    if (!loading && documentData && fileUrl) {
      // Initialize canvas first
      const canvasTimer = setTimeout(() => {
        initCanvas();
        
        // Then load annotations after canvas is ready - longer delay to ensure rendering
        setTimeout(() => {
          if (fabricCanvasRef.current && !initialLoadDone.current) {
            console.log('Loading annotations...');
            loadAnnotations();
            initialLoadDone.current = true;
            
            // Force another render after a short delay
            setTimeout(() => {
              if (fabricCanvasRef.current) {
                fabricCanvasRef.current.requestRenderAll();
              }
            }, 200);
          }
        }, 800);
      }, 600);
      
      return () => clearTimeout(canvasTimer);
    }
  }, [loading, documentData, fileUrl, initCanvas, loadAnnotations]);

  // Handle page change - reload annotations for new page
  useEffect(() => {
    if (canvasInitialized.current && fabricCanvasRef.current && initialLoadDone.current) {
      // When page changes, clear and reload
      fabricCanvasRef.current.clear();
      loadAnnotations();
    }
  }, [pageNumber, loadAnnotations]);

  // Update tool mode
  useEffect(() => {
    if (!fabricCanvasRef.current) return;

    const canvas = fabricCanvasRef.current;

    switch (activeTool) {
      case 'draw':
        canvas.isDrawingMode = true;
        if (!canvas.freeDrawingBrush) {
          canvas.freeDrawingBrush = new PencilBrush(canvas);
        }
        canvas.freeDrawingBrush.color = brushColor;
        canvas.freeDrawingBrush.width = brushWidth;
        break;
      case 'select':
        canvas.isDrawingMode = false;
        break;
      case 'rectangle':
      case 'circle':
      case 'arrow':
      case 'text':
        canvas.isDrawingMode = false;
        break;
      default:
        canvas.isDrawingMode = false;
    }
  }, [activeTool, brushColor, brushWidth]);

  const handleCanvasClick = (e) => {
    if (!fabricCanvasRef.current) return;
    const canvas = fabricCanvasRef.current;
    
    // Fabric.js v6 uses getScenePoint or we can calculate manually
    const canvasElement = canvas.getElement();
    const rect = canvasElement.getBoundingClientRect();
    const pointer = {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    };

    switch (activeTool) {
      case 'rectangle': {
        const newRect = new Rect({
          left: pointer.x,
          top: pointer.y,
          width: 100,
          height: 60,
          fill: 'transparent',
          stroke: brushColor,
          strokeWidth: brushWidth,
        });
        canvas.add(newRect);
        break;
      }
      case 'circle': {
        const circle = new Circle({
          left: pointer.x,
          top: pointer.y,
          radius: 50,
          fill: 'transparent',
          stroke: brushColor,
          strokeWidth: brushWidth,
        });
        canvas.add(circle);
        break;
      }
      case 'text': {
        if (textInput) {
          const text = new IText(textInput, {
            left: pointer.x,
            top: pointer.y,
            fill: brushColor,
            fontSize: 16 + brushWidth * 2,
            fontFamily: 'Arial',
          });
          canvas.add(text);
          setTextInput('');
        }
        break;
      }
      case 'arrow': {
        const line = new Line([pointer.x, pointer.y, pointer.x + 100, pointer.y], {
          stroke: brushColor,
          strokeWidth: brushWidth,
          selectable: true,
        });
        // Arrow head
        const triangle = new Triangle({
          left: pointer.x + 100,
          top: pointer.y,
          width: 15,
          height: 15,
          fill: brushColor,
          angle: 90,
          originX: 'center',
          originY: 'center',
        });
        const group = new Group([line, triangle], {
          selectable: true,
        });
        canvas.add(group);
        break;
      }
      default:
        break;
    }
  };

  const handleSave = async () => {
    if (!fabricCanvasRef.current) return;

    setIsSaving(true);
    try {
      const canvasJson = JSON.stringify(fabricCanvasRef.current.toJSON());

      await api.post('/api/annotations/', {
        document_id: parseInt(documentId, 10),
        page_number: pageNumber,
        content: canvasJson,
        annotation_type: 'canvas',
      });

      showNotification('Οι σημειώσεις αποθηκεύτηκαν!');
    } catch (_error) {
      console.error('Save error:', error);
      showNotification('Σφάλμα αποθήκευσης', 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const handleClear = () => {
    if (fabricCanvasRef.current) {
      fabricCanvasRef.current.clear();
    }
  };

  const handleDelete = () => {
    if (fabricCanvasRef.current) {
      const activeObjects = fabricCanvasRef.current.getActiveObjects();
      activeObjects.forEach((obj) => {
        fabricCanvasRef.current.remove(obj);
      });
      fabricCanvasRef.current.discardActiveObject();
      fabricCanvasRef.current.renderAll();
    }
  };

  const onDocumentLoadSuccess = ({ numPages }) => {
    setNumPages(numPages);
  };

  const tools = [
    { id: 'select', icon: '👆', label: 'Επιλογή' },
    { id: 'draw', icon: '✏️', label: 'Ελεύθερο σχέδιο' },
    { id: 'rectangle', icon: '⬜', label: 'Τετράγωνο' },
    { id: 'circle', icon: '⭕', label: 'Κύκλος' },
    { id: 'arrow', icon: '➡️', label: 'Βέλος' },
    { id: 'text', icon: '🔤', label: 'Κείμενο' },
  ];

  const colors = [
    '#FF0000',
    '#00FF00',
    '#0000FF',
    '#FFFF00',
    '#FF00FF',
    '#00FFFF',
    '#000000',
    '#FFFFFF',
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="text-6xl mb-4">📄</div>
          <p className="text-gray-600">Φόρτωση εγγράφου...</p>
        </div>
      </div>
    );
  }

  const isPdf = documentData?.file_type === 'pdf';

  return (
    <div className="flex flex-col h-full bg-gray-100">
      {/* Header */}
      <div className="bg-white border-b px-4 py-3 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate('/documents')}
            className="text-gray-600 hover:text-gray-900"
          >
            ← Πίσω
          </button>
          <h1 className="text-lg font-semibold text-gray-900 truncate max-w-md">
            {documentData?.title}
          </h1>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 disabled:opacity-50"
          >
            {isSaving ? '💾 Αποθήκευση...' : '💾 Αποθήκευση'}
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Toolbar */}
        <div className="w-20 bg-white border-r p-2 flex flex-col items-center space-y-2">
          {tools.map((tool) => (
            <button
              key={tool.id}
              onClick={() => setActiveTool(tool.id)}
              className={`w-14 h-14 rounded-lg flex flex-col items-center justify-center text-xs transition-colors ${
                activeTool === tool.id
                  ? 'bg-primary-100 text-primary-700 border-2 border-primary-500'
                  : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
              }`}
              title={tool.label}
            >
              <span className="text-lg mb-1">{tool.icon}</span>
              <span className="text-xs hidden lg:block">{tool.label}</span>
            </button>
          ))}

          <hr className="w-full my-2" />

          {/* Delete button */}
          <button
            onClick={handleDelete}
            className="w-14 h-14 rounded-lg flex flex-col items-center justify-center text-xs bg-red-50 text-red-600 hover:bg-red-100"
            title="Διαγραφή επιλογής"
          >
            <span className="text-lg mb-1">🗑️</span>
          </button>

          {/* Clear button */}
          <button
            onClick={handleClear}
            className="w-14 h-14 rounded-lg flex flex-col items-center justify-center text-xs bg-gray-50 text-gray-600 hover:bg-gray-100"
            title="Καθαρισμός όλων"
          >
            <span className="text-lg mb-1">🧹</span>
          </button>
        </div>

        {/* Canvas Area */}
        <div
          ref={containerRef}
          className="flex-1 relative overflow-auto bg-gray-200"
          onClick={handleCanvasClick}
        >
          {/* Document Viewer */}
          <div className="absolute inset-0 flex items-center justify-center p-4">
            {isPdf ? (
              <Document
                file={fileUrl}
                onLoadSuccess={onDocumentLoadSuccess}
                loading={<p>Φόρτωση PDF...</p>}
              >
                <Page pageNumber={pageNumber} scale={scale} />
              </Document>
            ) : (
              <img
                src={fileUrl}
                alt={documentData?.title}
                className="max-w-full max-h-full object-contain shadow-lg"
                style={{ transform: `scale(${scale})` }}
              />
            )}
          </div>

          {/* Fabric.js Canvas Overlay */}
          <div className="absolute inset-0 z-10 pointer-events-auto" style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}>
            <canvas
              ref={canvasRef}
              style={{ 
                cursor: activeTool === 'draw' ? 'crosshair' : 'default',
                width: '100%',
                height: '100%',
              }}
            />
          </div>
        </div>

        {/* Right Panel */}
        <div className="w-64 bg-white border-l p-4 overflow-y-auto">
          {/* Colors */}
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-900 mb-3">Χρώμα</h3>
            <div className="grid grid-cols-4 gap-2">
              {colors.map((color) => (
                <button
                  key={color}
                  onClick={() => setBrushColor(color)}
                  className={`w-8 h-8 rounded-md border-2 ${
                    brushColor === color ? 'border-gray-900 ring-2 ring-primary-500' : 'border-gray-300'
                  }`}
                  style={{ backgroundColor: color }}
                />
              ))}
            </div>
          </div>

          {/* Line Width */}
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-900 mb-3">Πάχος γραμμής: {brushWidth}px</h3>
            <input
              type="range"
              min="1"
              max="20"
              value={brushWidth}
              onChange={(e) => setBrushWidth(Number(e.target.value))}
              className="w-full"
            />
          </div>

          {/* Text Input (for text tool) */}
          {activeTool === 'text' && (
            <div className="mb-6">
              <h3 className="text-sm font-medium text-gray-900 mb-3">Κείμενο</h3>
              <input
                type="text"
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                placeholder="Πληκτρολογήστε κείμενο..."
                className="w-full border border-gray-300 rounded-md py-2 px-3 text-sm focus:ring-primary-500 focus:border-primary-500"
              />
              <p className="mt-2 text-xs text-gray-500">
                Γράψτε κείμενο και κλικ στο έγγραφο για να το τοποθετήσετε
              </p>
            </div>
          )}

          {/* Zoom */}
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-900 mb-3">Μεγέθυνση: {Math.round(scale * 100)}%</h3>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setScale((s) => Math.max(0.5, s - 0.2))}
                className="px-3 py-1 bg-gray-100 rounded text-sm hover:bg-gray-200"
              >
                -
              </button>
              <input
                type="range"
                min="0.5"
                max="3"
                step="0.1"
                value={scale}
                onChange={(e) => setScale(Number(e.target.value))}
                className="flex-1"
              />
              <button
                onClick={() => setScale((s) => Math.min(3, s + 0.2))}
                className="px-3 py-1 bg-gray-100 rounded text-sm hover:bg-gray-200"
              >
                +
              </button>
            </div>
          </div>

          {/* Page Navigation (for PDF) */}
          {isPdf && numPages && (
            <div className="mb-6">
              <h3 className="text-sm font-medium text-gray-900 mb-3">
                Σελίδα {pageNumber} από {numPages}
              </h3>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setPageNumber((p) => Math.max(1, p - 1))}
                  disabled={pageNumber <= 1}
                  className="flex-1 px-3 py-2 bg-gray-100 rounded text-sm hover:bg-gray-200 disabled:opacity-50"
                >
                  ← Προηγ.
                </button>
                <button
                  onClick={() => setPageNumber((p) => Math.min(numPages, p + 1))}
                  disabled={pageNumber >= numPages}
                  className="flex-1 px-3 py-2 bg-gray-100 rounded text-sm hover:bg-gray-200 disabled:opacity-50"
                >
                  Επόμ. →
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DocumentAnnotate;
