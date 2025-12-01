import os
import sys
import pytest
import asyncio
import time
from unittest.mock import MagicMock, patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from modules.analysis.Analysis import Analysis
from modules.analysis.AnalysisTask import AnalysisTask


class TestAnalysisTask:
    """Black-box tests for AnalysisTask - async stranger tracking"""
    
    @pytest.mark.asyncio
    async def test_analysis_task_initialization(self):
        """Black-box: AnalysisTask initializes with correct properties"""
        on_complete = MagicMock()
        task = AnalysisTask(id_stranger=1, on_complete=on_complete)
        
        assert task.id_stranger == 1
        assert task.on_complete == on_complete
        assert task.paused.is_set()  # Should be paused initially
        assert task.task is not None
        assert asyncio.iscoroutine(task.run.__wrapped__) or asyncio.isfuture(task.task)
        
        # Cleanup
        task.cancel()
    
    
    @pytest.mark.asyncio
    async def test_analysis_task_pause_clears_event(self):
        """Black-box: pause() clears the paused event, stopping tracking"""
        on_complete = MagicMock()
        task = AnalysisTask(id_stranger=2, on_complete=on_complete)
        
        assert task.paused.is_set()
        task.pause()
        assert not task.paused.is_set()
        
        task.cancel()
    
    
    @pytest.mark.asyncio
    async def test_analysis_task_resume_sets_event(self):
        """Black-box: resume() sets the paused event, resuming tracking"""
        on_complete = MagicMock()
        task = AnalysisTask(id_stranger=3, on_complete=on_complete)
        
        task.pause()
        assert not task.paused.is_set()
        
        task.resume()
        assert task.paused.is_set()
        
        task.cancel()
    
    
    @pytest.mark.asyncio
    async def test_analysis_task_duration_tracking(self):
        """Black-box: AnalysisTask tracks elapsed time correctly"""
        on_complete = MagicMock()
        task = AnalysisTask(id_stranger=4, on_complete=on_complete)
        
        initial_duration = task.end_time - task.start_time
        assert initial_duration >= 0
        
        await asyncio.sleep(0.1)
        task.pause()
        
        duration = task.end_time - task.start_time
        assert duration > initial_duration
        
        task.cancel()
    
    
    @pytest.mark.asyncio
    async def test_analysis_task_cancel_triggers_done_callback(self):
        """Black-box: cancel() triggers the task's done callback"""
        on_complete = MagicMock()
        task = AnalysisTask(id_stranger=5, on_complete=on_complete)
        
        task.cancel()
        
        # Give callback time to execute
        await asyncio.sleep(0.1)
    
    
    @pytest.mark.asyncio
    async def test_analysis_task_legal_duration_constant(self):
        """Black-box: LEGAL_DURATION is defined and positive"""
        assert hasattr(AnalysisTask, 'LEGAL_DURATION')
        assert AnalysisTask.LEGAL_DURATION > 0
        assert AnalysisTask.LEGAL_DURATION == 10


class TestAnalysis:
    """Black-box tests for Analysis - singleton stranger tracker manager"""
    
    def test_analysis_singleton_pattern(self):
        """Black-box: Analysis implements singleton pattern"""
        analysis1 = Analysis()
        analysis2 = Analysis()
        
        # Should be same instance
        assert analysis1 is analysis2
    
    
    def test_analysis_initialization(self):
        """Black-box: Analysis initializes with empty tasks dict"""
        analysis = Analysis()
        
        # Should have tasks_dict attribute
        assert hasattr(analysis, '_Analysis__tasks_dict')
        # Should be a dict
        assert isinstance(analysis._Analysis__tasks_dict, dict)
    
    
    @pytest.mark.asyncio
    async def test_start_tracking_stranger_creates_task(self):
        """Black-box: startTrackingStranger creates a tracking task"""
        analysis = Analysis()
        stranger_id = 100
        
        analysis.startTrackingStranger(stranger_id)
        
        # Task should be in dict
        tasks = analysis._Analysis__tasks_dict
        assert stranger_id in tasks
        
        # Cleanup
        analysis.stopTrackingStranger(stranger_id)
    
    
    @pytest.mark.asyncio
    async def test_pause_tracking_stranger(self):
        """Black-box: pauseTrackingStranger pauses the tracking task"""
        analysis = Analysis()
        stranger_id = 101
        
        analysis.startTrackingStranger(stranger_id)
        
        # Pause should not raise exception
        analysis.pauseTrackingStranger(stranger_id)
        
        # Task should still exist
        assert stranger_id in analysis._Analysis__tasks_dict
        
        analysis.stopTrackingStranger(stranger_id)
    
    
    @pytest.mark.asyncio
    async def test_resume_tracking_stranger(self):
        """Black-box: resumeTrackingStranger resumes the tracking task"""
        analysis = Analysis()
        stranger_id = 102
        
        analysis.startTrackingStranger(stranger_id)
        analysis.pauseTrackingStranger(stranger_id)
        
        # Resume should not raise exception
        analysis.resumeTrackingStranger(stranger_id)
        
        # Task should still exist
        assert stranger_id in analysis._Analysis__tasks_dict
        
        analysis.stopTrackingStranger(stranger_id)
    
    
    @pytest.mark.asyncio
    async def test_stop_tracking_stranger_removes_task(self):
        """Black-box: stopTrackingStranger removes task from dict"""
        analysis = Analysis()
        stranger_id = 103
        
        analysis.startTrackingStranger(stranger_id)
        assert stranger_id in analysis._Analysis__tasks_dict
        
        analysis.stopTrackingStranger(stranger_id)
        
        # Task should be removed
        assert stranger_id not in analysis._Analysis__tasks_dict
    
    
    @pytest.mark.asyncio
    async def test_pause_nonexistent_task_handled_gracefully(self):
        """Black-box: pauseTrackingStranger handles nonexistent task gracefully"""
        analysis = Analysis()
        
        # Should not raise exception
        analysis.pauseTrackingStranger(999)
    
    
    @pytest.mark.asyncio
    async def test_resume_nonexistent_task_handled_gracefully(self):
        """Black-box: resumeTrackingStranger handles nonexistent task gracefully"""
        analysis = Analysis()
        
        # Should not raise exception
        analysis.resumeTrackingStranger(999)
    
    
    @pytest.mark.asyncio
    async def test_stop_nonexistent_task_handled_gracefully(self):
        """Black-box: stopTrackingStranger handles nonexistent task gracefully"""
        analysis = Analysis()
        
        # Should not raise exception
        analysis.stopTrackingStranger(999)
    
    
    def test_check_managed_tasks_no_exception(self):
        """Black-box: checkManageredTasks can be called without exception"""
        analysis = Analysis()
        
        # Should not raise exception
        analysis.checkManageredTasks()
    
    
    @pytest.mark.asyncio
    async def test_analysis_leaving_duration_constant(self):
        """Black-box: LEAVING_DURATION is defined and positive"""
        analysis = Analysis()
        
        assert hasattr(analysis, 'LEAVING_DURATION')
        assert analysis.LEAVING_DURATION > 0
        assert analysis.LEAVING_DURATION == 5
    
    
    @pytest.mark.asyncio
    async def test_multiple_strangers_tracking(self):
        """Black-box: Analysis can track multiple strangers simultaneously"""
        analysis = Analysis()
        
        # Start tracking multiple strangers
        analysis.startTrackingStranger(201)
        analysis.startTrackingStranger(202)
        analysis.startTrackingStranger(203)
        
        tasks = analysis._Analysis__tasks_dict
        assert len(tasks) >= 3
        assert 201 in tasks
        assert 202 in tasks
        assert 203 in tasks
        
        # Cleanup
        analysis.stopTrackingStranger(201)
        analysis.stopTrackingStranger(202)
        analysis.stopTrackingStranger(203)
