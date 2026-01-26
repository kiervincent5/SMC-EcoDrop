/**
 * Rewards Page Interactions
 * Handles redemption modals, quantity selection, and points calculation.
 */

var RewardsManager = (function () {
    var userPoints = 0;
    var currentRewardPoints = 0;

    /**
     * Initialize the rewards manager with the user's current points.
     * @param {number} points - The total points available for the user.
     */
    function init(points) {
        userPoints = parseInt(points) || 0;
        setupEventListeners();
        setupSuccessModal();
    }

    function setupEventListeners() {
        // Event delegation for redeem buttons
        document.addEventListener('click', function (e) {
            if (e.target.classList.contains('redeem-btn') && !e.target.disabled) {
                var rewardId = e.target.getAttribute('data-reward-id');
                var rewardName = e.target.getAttribute('data-reward-name');
                var requiredPoints = parseInt(e.target.getAttribute('data-reward-points'));
                var colorClass = e.target.getAttribute('data-reward-color');

                if (rewardId && rewardName && requiredPoints) {
                    openRedeemModal(rewardId, rewardName, requiredPoints, colorClass);
                }
            }
        });

        // Quantity controls
        var qIncrease = document.getElementById('quantityIncrease');
        if (qIncrease) {
            qIncrease.addEventListener('click', function () {
                var input = document.getElementById('quantityInput');
                var currentVal = parseInt(input.value) || 1;
                input.value = currentVal + 1;
                updatePointsCalculation();
            });
        }

        var qDecrease = document.getElementById('quantityDecrease');
        if (qDecrease) {
            qDecrease.addEventListener('click', function () {
                var input = document.getElementById('quantityInput');
                var currentVal = parseInt(input.value) || 1;
                if (currentVal > 1) {
                    input.value = currentVal - 1;
                    updatePointsCalculation();
                }
            });
        }

        var qInput = document.getElementById('quantityInput');
        if (qInput) {
            qInput.addEventListener('input', function () {
                updatePointsCalculation();
            });
        }

        // Modal triggers
        var closeBtn = document.getElementById('modalCloseBtn');
        if (closeBtn) closeBtn.addEventListener('click', closeRedeemModal);
        
        var cancelBtn = document.getElementById('modalCancelBtn');
        if (cancelBtn) cancelBtn.addEventListener('click', closeRedeemModal);

        // Click overlay to close
        var redeemModal = document.getElementById('redeemModal');
        if (redeemModal) {
            redeemModal.addEventListener('click', function (e) {
                if (e.target === this) {
                    closeRedeemModal();
                }
            });
        }

        // Close modal on Escape key
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') {
                closeRedeemModal();
            }
        });
    }

    function openRedeemModal(rewardId, rewardName, requiredPoints, colorClass) {
        currentRewardPoints = requiredPoints;

        // Reset quantity to 1
        var qInput = document.getElementById('quantityInput');
        var qHidden = document.getElementById('quantityHiddenInput');
        if (qInput) qInput.value = 1;
        if (qHidden) qHidden.value = 1;

        // Update modal content
        var modalName = document.getElementById('modalRewardName');
        if (modalName) modalName.textContent = rewardName;
        
        var modalPoints = document.getElementById('modalPointsPerItem');
        if (modalPoints) modalPoints.textContent = '-' + requiredPoints + ' pts';

        // Update header color
        var modalHeader = document.getElementById('modalHeaderColor');
        if (modalHeader) {
            modalHeader.className = 'modal-header ' + colorClass;
        }

        // Update form action
        var redeemForm = document.getElementById('redeemForm');
        if (redeemForm) {
            redeemForm.action = '/redeem/' + rewardId + '/';
        }

        // Calculate and update points
        updatePointsCalculation();

        // Show modal
        var modal = document.getElementById('redeemModal');
        if (modal) modal.classList.add('active');
    }

    function updatePointsCalculation() {
        var qInput = document.getElementById('quantityInput');
        var quantity = parseInt(qInput ? qInput.value : 1) || 1;
        if (quantity < 1) quantity = 1;

        var totalRequired = currentRewardPoints * quantity;
        var afterPoints = userPoints - totalRequired;

        // Update displays
        var reqPointsDisplay = document.getElementById('modalRequiredPoints');
        if (reqPointsDisplay) reqPointsDisplay.textContent = '-' + totalRequired + ' pts';
        
        var afterPointsDisplay = document.getElementById('modalAfterPoints');
        if (afterPointsDisplay) afterPointsDisplay.textContent = afterPoints + ' pts';
        
        var qHidden = document.getElementById('quantityHiddenInput');
        if (qHidden) qHidden.value = quantity;

        // Show/hide badges and enable/disable button based on points
        var readyBadge = document.getElementById('readyBadge');
        var insufficientBadge = document.getElementById('insufficientBadge');
        var confirmBtn = document.getElementById('confirmRedeemBtn');

        if (afterPoints >= 0) {
            if (readyBadge) readyBadge.style.display = 'flex';
            if (insufficientBadge) insufficientBadge.style.display = 'none';
            if (confirmBtn) {
                confirmBtn.disabled = false;
                confirmBtn.style.opacity = '1';
                confirmBtn.style.cursor = 'pointer';
            }
        } else {
            if (readyBadge) readyBadge.style.display = 'none';
            if (insufficientBadge) insufficientBadge.style.display = 'flex';
            if (confirmBtn) {
                confirmBtn.disabled = true;
                confirmBtn.style.opacity = '0.5';
                confirmBtn.style.cursor = 'not-allowed';
            }
        }
    }

    function closeRedeemModal() {
        var modal = document.getElementById('redeemModal');
        if (modal) modal.classList.remove('active');
    }

    function setupSuccessModal() {
        var successModal = document.getElementById('successModal');
        if (successModal) {
            function closeSuccessModal() {
                successModal.classList.remove('active');
            }

            var successCloseBtn = document.getElementById('successCloseBtn');
            if (successCloseBtn) {
                successCloseBtn.addEventListener('click', closeSuccessModal);
            }

            var successDoneBtn = document.getElementById('successDoneBtn');
            if (successDoneBtn) {
                successDoneBtn.addEventListener('click', closeSuccessModal);
            }

            successModal.addEventListener('click', function (e) {
                if (e.target === this) {
                    closeSuccessModal();
                }
            });

            document.addEventListener('keydown', function (e) {
                if (e.key === 'Escape' && successModal.classList.contains('active')) {
                    closeSuccessModal();
                }
            });
        }
    }

    return {
        init: init
    };
})();
